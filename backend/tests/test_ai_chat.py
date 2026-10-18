"""对话编排测试：用脚本化的假适配器驱动，覆盖工具循环、持久化、上下文与后台任务。"""
import asyncio
import json
from datetime import date

import pytest

from apps.ai.adapters import ChatResponse, ToolCall
from apps.ai.models import AIModelConfig, ChatMessage, ChatSession
from apps.ai.services import chat, session as session_service
from apps.bills.models import Bill
from apps.categories.models import Category
from apps.users.models import User

pytestmark = pytest.mark.django_db(transaction=True)  # 异步代码走独立线程，需要真实提交


class FakeAdapter:
    """rounds：每次调用主对话时依次消费的统一流式事件列表。不带工具的调用（标题、摘要）返回 aux。"""

    def __init__(self, rounds, aux="记账标题"):
        self.rounds, self.aux, self.calls = list(rounds), aux, []

    async def chat_stream(self, messages, tools):
        self.calls.append(messages)
        for event in self.rounds.pop(0):
            yield event

    async def chat(self, messages, tools):
        if not tools:
            return ChatResponse(content=self.aux)
        self.calls.append(messages)
        text, calls = "", {}
        for e in self.rounds.pop(0):
            if e["type"] == "text_delta":
                text += e["content"]
            elif e["type"] == "tool_call_start":
                calls[e["tool_call_id"]] = [e["tool_name"], ""]
            elif e["type"] == "tool_call_delta":
                calls[e["tool_call_id"]][1] += e["arguments_delta"]
        return ChatResponse(content=text or None, stop_reason="tool_use" if calls else "end_turn",
                            tool_calls=[ToolCall(i, n, json.loads(a or "{}")) for i, (n, a) in calls.items()])


def text(s):
    return [{"type": "text_delta", "content": s}, {"type": "done", "stop_reason": "end_turn"}]


def tool(call_id, name, args, preface=""):
    events = [{"type": "text_delta", "content": preface}] if preface else []
    return events + [
        {"type": "tool_call_start", "tool_call_id": call_id, "tool_name": name},
        {"type": "tool_call_delta", "tool_call_id": call_id, "arguments_delta": json.dumps(args)[:5]},
        {"type": "tool_call_delta", "tool_call_id": call_id, "arguments_delta": json.dumps(args)[5:]},
        {"type": "tool_call_end", "tool_call_id": call_id},
        {"type": "done", "stop_reason": "tool_use"},
    ]


@pytest.fixture
def ai_config(user):
    return AIModelConfig.objects.create(user=user, name="t", provider="deepseek", api_key="k",
                                        model="m", is_default=True)


@pytest.fixture
def fake(monkeypatch):
    def install(*rounds, **kw):
        adapter = FakeAdapter(rounds, **kw)
        monkeypatch.setattr(chat, "get_adapter", lambda cfg: adapter)
        return adapter
    return install


@pytest.fixture
def categories(user):
    return {
        "food": Category.objects.create(user=None, name="餐饮", type="expense", icon="🍔", is_default=True),
        "mine": Category.objects.create(user=user, name="宠物", type="expense", icon="🐶"),
    }


def run_stream(user, payload):
    async def go():
        events = [e async for e in chat.stream(user, payload)]
        await asyncio.gather(*chat._background)  # 等标题 / 摘要后台任务结束
        return events
    return asyncio.run(go())


def names(events):
    return [e["event"] for e in events]


def roles(session_id):
    return list(ChatMessage.objects.filter(session_id=session_id).values_list("role", flat=True))


# ---------------------------------------------------------------- 基本对话

def test_plain_reply_is_streamed_and_saved(user, ai_config, fake):
    adapter = fake(text("你好呀"))
    events = run_stream(user, {"message": "你好"})

    assert names(events) == ["session_created", "thinking", "text_delta", "done"]
    sid = events[0]["data"]["session_id"]
    assert events[-1]["data"]["session_id"] == sid and events[-1]["data"]["thinking_time_ms"] >= 0
    assert roles(sid) == ["user", "assistant"]
    assert ChatSession.objects.get(id=sid).title == "记账标题"  # 首轮对话后台生成标题

    # 系统提示词包含今天的日期与分类
    system = adapter.calls[0][0]
    assert system["role"] == "system" and date.today().isoformat() in system["content"]
    assert adapter.calls[0][1] == {"role": "user", "content": "你好"}


def test_system_prompt_lists_user_and_default_categories(user, ai_config, categories, fake):
    adapter = fake(text("ok"))
    run_stream(user, {"message": "hi"})
    prompt = adapter.calls[0][0]["content"]
    assert "餐饮" in prompt and "宠物" in prompt


def test_follow_up_message_reuses_session_and_history(user, ai_config, fake):
    adapter = fake(text("第一"), text("第二"))
    sid = run_stream(user, {"message": "a"})[0]["data"]["session_id"]
    events = run_stream(user, {"message": "b", "session_id": sid})
    assert events[0]["data"]["session_id"] == sid
    history = [m for m in adapter.calls[1] if m["role"] != "system"]
    assert [(m["role"], m["content"]) for m in history] == [("user", "a"), ("assistant", "第一"), ("user", "b")]
    assert roles(sid) == ["user", "assistant", "user", "assistant"]


def test_images_are_stored_and_sent_as_blocks(user, ai_config, fake):
    adapter = fake(text("看到了"))
    sid = run_stream(user, {"message": "这个多少钱", "images": ["QUJD"]})[0]["data"]["session_id"]
    assert json.loads(ChatMessage.objects.get(session_id=sid, role="user").image_url) == ["QUJD"]
    assert adapter.calls[0][1]["content"] == [{"type": "text", "text": "这个多少钱"},
                                              {"type": "image", "data": "QUJD", "media_type": "image/jpeg"}]


# ---------------------------------------------------------------- 工具循环

def test_create_bills_enriches_but_does_not_save(user, ai_config, categories, fake):
    args = {"bills": [{"amount": 32, "type": "expense", "description": "午饭", "categoryName": "餐饮",
                       "date": "2026-10-18"},
                      {"amount": 50, "type": "expense", "description": "猫粮", "categoryName": "宠物",
                       "date": "2026-10-18"},
                      {"amount": 5, "type": "expense", "description": "?", "categoryName": "不存在",
                       "date": "2026-10-18"}]}
    adapter = fake(tool("c1", "create_bills", args, preface="好的，"), text("已识别 3 条"))
    events = run_stream(user, {"message": "午饭32，猫粮50"})

    assert names(events) == ["session_created", "thinking", "text_delta", "tool_call_start", "tool_result",
                             "thinking", "text_delta", "done"]
    result = next(e for e in events if e["event"] == "tool_result")["data"]
    assert result["tool_call_id"] == "c1" and result["result"]["success"]
    bills = result["result"]["data"]["bills"]
    assert [b["categoryId"] for b in bills] == [categories["food"].id, categories["mine"].id, None]
    assert bills[0]["categoryIcon"] == "🍔"
    assert Bill.objects.count() == 0  # 只补全，由前端确认后保存

    sid = events[0]["data"]["session_id"]
    assert roles(sid) == ["user", "assistant", "tool", "assistant"]
    saved = ChatMessage.objects.get(session_id=sid, role="assistant", tool_calls__isnull=False)
    assert saved.content == "好的，" and saved.tool_calls[0]["arguments"] == args
    # 第二轮请求带上了 assistant(tool_calls) 与 tool 结果
    second = adapter.calls[1]
    assert [m["role"] for m in second[-3:]] == ["user", "assistant", "tool"]
    assert second[-1]["tool_call_id"] == "c1"


def test_query_and_statistics_tools(user, ai_config, categories, fake):
    Bill.objects.create(user=user, amount=30, type="expense", date="2026-10-01", category=categories["food"],
                        description="早饭")
    Bill.objects.create(user=user, amount=100, type="income", date="2026-10-02")
    other = User.objects.create_user("bob", "secret123")
    Bill.objects.create(user=other, amount=999, type="expense", date="2026-10-01")

    fake(tool("q", "query_bills", {"type": "expense", "categoryName": "餐饮"}),
         tool("s", "get_statistics", {"startDate": "2026-10-01", "endDate": "2026-10-31"}),
         text("总结"))
    events = run_stream(user, {"message": "这个月花了多少"})
    q, s = [e["data"]["result"] for e in events if e["event"] == "tool_result"]
    assert [i["description"] for i in q["data"]["items"]] == ["早饭"] and q["data"]["total"] == 1
    assert s["data"]["total_expense"] == 30 and s["data"]["total_income"] == 100  # 看不到别人的 999
    assert names(events).count("thinking") == 3


def test_delete_bills_only_own(user, ai_config, fake):
    mine = Bill.objects.create(user=user, amount=1, type="expense", date="2026-10-01")
    other = User.objects.create_user("bob", "secret123")
    theirs = Bill.objects.create(user=other, amount=2, type="expense", date="2026-10-01")
    fake(tool("d", "delete_bills", {"billIds": [mine.id, theirs.id, 99999]}), text("删好了"))

    result = next(e for e in run_stream(user, {"message": "删掉"}) if e["event"] == "tool_result")["data"]["result"]
    assert result["data"]["successCount"] == 1
    assert [r["deleted"] for r in result["data"]["results"]] == [True, False, False]
    assert not Bill.objects.filter(id=mine.id).exists() and Bill.objects.filter(id=theirs.id).exists()


def test_tool_failure_is_reported_to_model_not_raised(user, ai_config, fake):
    adapter = fake(tool("s", "get_statistics", {"startDate": "不是日期"}), text("抱歉，日期有误"))
    events = run_stream(user, {"message": "统计"})
    result = next(e for e in events if e["event"] == "tool_result")["data"]["result"]
    assert result["success"] is False and "get_statistics" in result["message"]
    assert names(events)[-1] == "done"
    assert json.loads(json.dumps(adapter.calls[1][-1]["tool_result"]))["success"] is False


def test_unknown_tool_name(user, ai_config, fake):
    fake(tool("x", "hack_the_planet", {}), text("好"))
    result = next(e for e in run_stream(user, {"message": "hi"}) if e["event"] == "tool_result")
    assert result["data"]["result"] == {"success": False, "data": None, "message": "未知工具: hack_the_planet"}


def test_tool_loop_stops_at_max_rounds(user, ai_config, fake):
    fake(*[tool(f"c{i}", "get_statistics", {}) for i in range(chat.MAX_TOOL_ROUNDS + 3)])
    events = run_stream(user, {"message": "循环"})
    assert names(events).count("thinking") == chat.MAX_TOOL_ROUNDS
    assert names(events)[-1] == "done"


def test_tool_call_without_name_is_ignored(user, ai_config, fake):
    fake([{"type": "tool_call_delta", "tool_call_id": "z", "arguments_delta": "{}"},
          {"type": "done", "stop_reason": "tool_use"}])
    events = run_stream(user, {"message": "hi"})
    assert "tool_result" not in names(events) and names(events)[-1] == "done"


# ---------------------------------------------------------------- 配置与会话归属

def test_no_ai_config_yields_error_event_and_no_empty_session(user, fake):
    fake()
    events = run_stream(user, {"message": "hi"})
    assert events == [{"event": "error", "data": {"message": "请先配置 AI 模型"}}]
    assert ChatSession.objects.count() == 0


def test_cannot_use_other_users_session_or_config(user, ai_config, fake):
    other = User.objects.create_user("bob", "secret123")
    foreign_session = ChatSession.objects.create(user=other)
    foreign_config = AIModelConfig.objects.create(user=other, name="x", provider="openai", api_key="k", model="m")
    fake()
    assert run_stream(user, {"message": "a", "session_id": foreign_session.id})[0]["data"]["message"] == "会话不存在"
    assert run_stream(user, {"message": "a", "ai_config_id": foreign_config.id})[0]["data"]["message"] \
        == "AI 模型配置不存在"


def test_session_remembers_explicit_config(user, ai_config, fake, monkeypatch):
    picked = []
    other_cfg = AIModelConfig.objects.create(user=user, name="y", provider="qwen", api_key="k", model="q")
    adapter = FakeAdapter([text("1"), text("2")])
    monkeypatch.setattr(chat, "get_adapter", lambda cfg: picked.append(cfg.id) or adapter)
    sid = run_stream(user, {"message": "a", "ai_config_id": other_cfg.id})[0]["data"]["session_id"]
    run_stream(user, {"message": "b", "session_id": sid})
    assert picked == [other_cfg.id, other_cfg.id]  # 第二次没传配置，沿用会话上的


def test_falls_back_to_any_config_when_no_default(user, fake, monkeypatch):
    cfg = AIModelConfig.objects.create(user=user, name="x", provider="qwen", api_key="k", model="q")
    picked = []
    adapter = FakeAdapter([text("ok")])
    monkeypatch.setattr(chat, "get_adapter", lambda c: picked.append(c.id) or adapter)
    run_stream(user, {"message": "hi"})
    assert picked == [cfg.id]


def test_adapter_exception_becomes_error_event(user, ai_config, monkeypatch):
    class Boom:
        async def chat_stream(self, messages, tools):
            raise RuntimeError("401 invalid api key")
            yield

    monkeypatch.setattr(chat, "get_adapter", lambda cfg: Boom())
    events = run_stream(user, {"message": "hi"})
    assert names(events) == ["session_created", "thinking", "error"]
    assert "401 invalid api key" in events[-1]["data"]["message"]


# ---------------------------------------------------------------- 上下文处理

def msg(role, content=None, **kw):
    return {"role": role, "content": content, **kw}


def test_sanitize_drops_orphans():
    call = [{"id": "a", "name": "n", "arguments": {}}]
    # 开头是裁剪后残留的 tool / assistant：丢到第一条 user 为止
    cut = [msg("tool", tool_call_id="a"), msg("assistant", "x"), msg("user", "hi"), msg("assistant", "ok")]
    assert [m["role"] for m in session_service.sanitize(cut)] == ["user", "assistant"]
    # tool_calls 没有结果（流被中断）：去掉 tool_calls，保留文字；无文字则整条丢弃
    interrupted = [msg("user", "hi"), msg("assistant", "稍等", tool_calls=call), msg("user", "在吗")]
    out = session_service.sanitize(interrupted)
    assert out[1]["content"] == "稍等" and not out[1]["tool_calls"]
    assert [m["role"] for m in session_service.sanitize(
        [msg("user", "hi"), msg("assistant", None, tool_calls=call), msg("user", "在吗")])] == ["user", "user"]
    # 完整的调用保持不变
    ok = [msg("user", "hi"), msg("assistant", None, tool_calls=call), msg("tool", tool_call_id="a")]
    assert session_service.sanitize(ok) == ok


def test_interrupted_tool_call_does_not_poison_session(user, ai_config, fake):
    session = session_service.create_session(user)
    session_service.append_message(session, "user", content="记一笔")
    session_service.append_message(session, "assistant", content=None,
                                   tool_calls=[{"id": "lost", "name": "create_bills", "arguments": {}}])
    adapter = fake(text("继续"))
    run_stream(user, {"message": "还在吗", "session_id": session.id})
    sent = [m for m in adapter.calls[0] if m["role"] != "system"]
    assert [m["role"] for m in sent] == ["user", "user"] and not any(m.get("tool_calls") for m in sent)


def test_context_is_trimmed_without_cutting_tool_pairs(user):
    session = session_service.create_session(user)
    call = [{"id": "k", "name": "get_statistics", "arguments": {}}]
    session_service.append_message(session, "user", content="旧")
    session_service.append_message(session, "assistant", content=None, tool_calls=call)
    session_service.append_message(session, "tool", tool_call_id="k", tool_name="get_statistics", tool_result={})
    session_service.append_message(session, "user", content="新")
    # 只留最后 2 条会切在 tool 上：应从 user 重新开始
    assert [m["role"] for m in session_service.build_context(session, max_messages=2)] == ["user"]


# ---------------------------------------------------------------- 摘要压缩

def test_old_messages_are_summarized(user, ai_config, fake):
    session = session_service.create_session(user)
    for i in range(chat.SUMMARY_THRESHOLD):
        session_service.append_message(session, "user" if i % 2 == 0 else "assistant", content=f"消息{i}")
    adapter = fake(text("好"), aux="摘要内容")
    run_stream(user, {"message": "再来一条", "session_id": session.id})

    session.refresh_from_db()
    assert session.summary == "摘要内容"
    # 保留最近 SUMMARY_KEEP_RECENT 条：总共 22 条，压缩前 12 条
    assert session.summary_up_to == 22 - chat.SUMMARY_KEEP_RECENT
    # 下一轮上下文 = 摘要 + 未压缩的消息
    ctx = session_service.build_context(session)
    assert ctx[0]["role"] == "system" and "摘要内容" in ctx[0]["content"]
    assert len(ctx) - 1 <= chat.SUMMARY_KEEP_RECENT + 1


def test_few_messages_are_not_summarized(user, ai_config, fake):
    fake(text("好"))
    sid = run_stream(user, {"message": "a"})[0]["data"]["session_id"]
    assert ChatSession.objects.get(id=sid).summary is None


# ---------------------------------------------------------------- 非流式与 HTTP 接口

def test_send_endpoint(client, user, ai_config, categories, fake):
    fake(tool("c", "create_bills", {"bills": [{"amount": 8, "type": "expense", "description": "咖啡",
                                              "categoryName": "餐饮", "date": "2026-10-18"}]},
              preface="我来记账。"),
         text("记好了"))
    resp = client.post("/api/ai/chat/send", {"message": "咖啡8块"}, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["content"] == "记好了"  # 只取最后一轮，不含"我来记账。"
    assert data["sessionId"] and data["toolResults"][0]["toolName"] == "create_bills"
    assert data["toolResults"][0]["result"]["data"]["bills"][0]["categoryId"] == categories["food"].id


def test_send_without_config_is_400(client, fake):
    fake()
    resp = client.post("/api/ai/chat/send", {"message": "hi"}, format="json")
    assert resp.status_code == 400 and resp.json()["message"] == "请先配置 AI 模型"


def test_send_provider_failure_is_502(client, ai_config, monkeypatch):
    class Boom:
        async def chat(self, messages, tools):
            raise RuntimeError("upstream down")

    monkeypatch.setattr(chat, "get_adapter", lambda cfg: Boom())
    resp = client.post("/api/ai/chat/send", {"message": "hi"}, format="json")
    assert resp.status_code == 502 and "upstream down" in resp.json()["message"]


def test_send_rejects_empty_message(client, ai_config):
    assert client.post("/api/ai/chat/send", {"message": "  "}, format="json").status_code == 400


def test_stream_endpoint_end_to_end(client, ai_config, fake):
    from django.test import Client

    fake(text("流式回复"))
    token = client._credentials["HTTP_AUTHORIZATION"]
    resp = Client().post("/api/ai/chat/stream", {"message": "你好"}, content_type="application/json",
                         HTTP_AUTHORIZATION=token)

    async def read():
        body = b"".join([c async for c in resp.streaming_content])
        await asyncio.gather(*chat._background)
        return body.decode()

    body = asyncio.run(read())
    assert '"event": "session_created"' in body and '"sessionId"' in body
    assert "流式回复" in body and '"thinkingTimeMs"' in body


def test_large_base64_images_are_accepted_by_stream(client, ai_config, fake):
    """流式接口直接读 request.body，受 DATA_UPLOAD_MAX_MEMORY_SIZE 约束（默认 2.5MB）。
    3 张约 1MB 的 Base64 图片合计超过默认值。"""
    from django.test import Client

    adapter = fake(text("看到了"))
    images = ["data:image/jpeg;base64," + "A" * 1_000_000 for _ in range(3)]
    resp = Client().post("/api/ai/chat/stream", {"message": "这些多少钱", "images": images},
                         content_type="application/json", HTTP_AUTHORIZATION=client._credentials["HTTP_AUTHORIZATION"])

    async def read():
        body = b"".join([c async for c in resp.streaming_content])
        await asyncio.gather(*chat._background)
        return body.decode()

    assert resp.status_code == 200 and "看到了" in asyncio.run(read())
    assert [b["type"] for b in adapter.calls[0][1]["content"]] == ["text", "image", "image", "image"]
