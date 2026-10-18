"""
对话编排。对应原项目 ai/services/chat.service.ts。

一次对话的流程（_run）：
  1. 取会话（没有则创建）与 AI 配置，推送 session_created
  2. 保存用户消息（含图片）
  3. build_context() 组装上下文 + 系统提示词
  4. 调用适配器；若返回 tool_calls：
       保存 assistant 消息 → 逐个 tool_executor.execute() → 保存 tool 消息 → 再次调用适配器
     循环直到没有 tool_calls 或达到 MAX_TOOL_ROUNDS
  5. 保存最终 assistant 回复；首轮对话后台生成会话标题，消息过多时后台压缩为摘要

流式与非流式共用同一个循环，区别只在调用 adapter.chat_stream 还是 adapter.chat。

流式事件（推送给前端，SSE `data: {"event": ..., "data": {...}}`）：
  session_created / thinking / thinking_delta / text_delta / tool_call_start / tool_result / done / error
"""
import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import Q
from django.utils import timezone

from apps.categories.models import Category
from common.exceptions import BusinessError

from ..adapters import get_adapter
from ..models import ChatSession
from ..tools import TOOLS
from . import session as sessions
from . import tool_executor
from .configs import resolve_ai_config

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5
SUMMARY_THRESHOLD = 20  # 未摘要消息达到这个数量就触发压缩
SUMMARY_KEEP_RECENT = 10  # 压缩时保留最近的消息不动

WEEKDAYS = "一二三四五六日"

SYSTEM_PROMPT = """你是一个智能助手，可以帮助用户记账、查询账单、统计分析，也可以进行日常闲聊和回答问题。

## 当前信息
- 今天是 {today}（星期{weekday}）

## 用户的账单分类
- 支出分类: {expense_categories}
- 收入分类: {income_categories}

## 工具使用规则
1. 当用户提到了消费或收入，且信息足够完整（至少有金额），调用 create_bills 工具
2. 如果用户表达了记账意图但信息不完整（缺少金额等关键信息），请友好地追问
3. 当用户想查看账单记录时，调用 query_bills 工具
4. 当用户要求删除账单时，调用 delete_bills 工具（需要先通过 query_bills 获取账单 ID）
5. 当用户询问统计、消费分析、预算等问题时，调用 get_statistics 工具
6. 日常闲聊和普通问答时，直接回复，不要调用任何工具

## 注意事项
- 如果用户没有指定日期，默认使用今天 ({today})
- 分类名称必须从上面列出的分类中选择
- 金额必须是正数
- 回复要简洁友好，使用中文"""

# 后台任务（标题、摘要）要持有引用，否则可能被垃圾回收
_background: set[asyncio.Task] = set()


# ---------------------------------------------------------------- 同步的数据库步骤（用 sync_to_async 调用）

def _prepare(user, payload: dict) -> dict:
    """校验会话与 AI 配置。找不到时抛 BusinessError，此时不会产生空会话。"""
    session = None
    if payload.get("session_id"):
        session = ChatSession.objects.filter(user=user, id=payload["session_id"], is_active=True).first()
        if session is None:
            raise BusinessError("会话不存在", status=404)

    ai_config = resolve_ai_config(user, payload.get("ai_config_id"), session.ai_config_id if session else None)

    is_new = session is None
    if is_new:
        session = sessions.create_session(user, ai_config=ai_config if payload.get("ai_config_id") else None)
    return {"session": session, "ai_config": ai_config, "is_new": is_new}


def _save_user_message(session, payload: dict):
    fields = {"content": payload.get("message") or None}
    if payload.get("images"):
        fields["image_url"] = json.dumps(payload["images"])
    sessions.append_message(session, "user", **fields)


def _build_messages(user, session) -> list[dict]:
    categories = Category.objects.filter(Q(user=user) | Q(user__isnull=True))
    names = lambda type_: "、".join(dict.fromkeys(c.name for c in categories if c.type == type_))  # noqa: E731
    today = timezone.localdate()
    prompt = SYSTEM_PROMPT.format(today=today.isoformat(), weekday=WEEKDAYS[today.weekday()],
                                  expense_categories=names("expense"), income_categories=names("income"))
    return [{"role": "system", "content": prompt}, *sessions.build_context(session)]


def _save_assistant(session, content, tool_calls=None):
    sessions.append_message(session, "assistant", content=content or None, tool_calls=tool_calls)


def _save_tool_result(session, call: dict, result: dict):
    sessions.append_message(session, "tool", tool_call_id=call["id"], tool_name=call["name"], tool_result=result)


# ---------------------------------------------------------------- 模型调用

async def _model_events(adapter, messages: list[dict], streaming: bool) -> AsyncIterator[dict]:
    """统一成适配器流式事件；非流式时把完整响应拆成同样的事件，上层循环不用区分。"""
    if streaming:
        async for event in adapter.chat_stream(messages, TOOLS):
            yield event
        return
    response = await adapter.chat(messages, TOOLS)
    if response.content:
        yield {"type": "text_delta", "content": response.content}
    for call in response.tool_calls:
        yield {"type": "tool_call_start", "tool_call_id": call.id, "tool_name": call.name}
        yield {"type": "tool_call_delta", "tool_call_id": call.id, "arguments_delta": json.dumps(call.arguments)}
    yield {"type": "done", "stop_reason": response.stop_reason}


def _parse_tool_calls(buffers: dict) -> list[dict]:
    calls = []
    for call_id, buf in buffers.items():
        if not buf["name"]:
            logger.warning("过滤掉没有名称的工具调用: %s", call_id)
            continue
        try:
            arguments = json.loads(buf["arguments"] or "{}")
        except json.JSONDecodeError:
            logger.warning("解析工具参数失败: %s", buf["arguments"])
            arguments = {}
        calls.append({"id": call_id, "name": buf["name"], "arguments": arguments})
    return calls


async def _run(user, payload: dict, streaming: bool) -> AsyncIterator[dict]:
    started = time.monotonic()
    prepared = await sync_to_async(_prepare)(user, payload)
    session, ai_config = prepared["session"], prepared["ai_config"]
    adapter = get_adapter(ai_config)

    yield {"event": "session_created", "data": {"session_id": session.id}}

    # 用户消息必须先入库再构建上下文，否则上下文里缺少当前这句话
    await sync_to_async(_save_user_message)(session, payload)
    messages = await sync_to_async(_build_messages)(user, session)

    for round_no in range(1, MAX_TOOL_ROUNDS + 1):
        yield {"event": "thinking", "data": {"round": round_no}}

        text, stop_reason, buffers = "", "end_turn", {}
        async for ev in _model_events(adapter, messages, streaming):
            kind = ev["type"]
            if kind == "text_delta":
                text += ev["content"]
                yield {"event": "text_delta", "data": {"content": ev["content"]}}
            elif kind == "thinking_delta":
                yield {"event": "thinking_delta", "data": {"content": ev["content"]}}
            elif kind == "tool_call_start":
                buf = buffers.setdefault(ev["tool_call_id"], {"name": "", "arguments": ""})
                buf["name"] = ev["tool_name"]
                yield {"event": "tool_call_start",
                       "data": {"tool_call_id": ev["tool_call_id"], "tool_name": ev["tool_name"]}}
            elif kind == "tool_call_delta":
                buf = buffers.setdefault(ev["tool_call_id"], {"name": "", "arguments": ""})
                buf["arguments"] += ev["arguments_delta"]
            elif kind == "done":
                stop_reason = ev["stop_reason"]

        # 有有效的工具调用就执行。不只看 stop_reason：个别兼容厂商带着工具调用却返回 "stop"
        calls = _parse_tool_calls(buffers)
        if not calls:
            if stop_reason == "tool_use":
                logger.warning("第 %s 轮声明了工具调用但没有有效内容，结束循环", round_no)
            if text:
                await sync_to_async(_save_assistant)(session, text)
            break

        await sync_to_async(_save_assistant)(session, text, calls)
        messages.append({"role": "assistant", "content": text or None, "tool_calls": calls})
        for call in calls:
            result = await sync_to_async(tool_executor.execute)(user, call["name"], call["arguments"])
            await sync_to_async(_save_tool_result)(session, call, result)
            messages.append({"role": "tool", "tool_call_id": call["id"], "tool_name": call["name"],
                             "tool_result": result})
            yield {"event": "tool_result",
                   "data": {"tool_call_id": call["id"], "tool_name": call["name"], "result": result}}
    else:
        logger.warning("会话 %s 工具调用达到 %s 轮上限", session.id, MAX_TOOL_ROUNDS)

    task = asyncio.create_task(_after_chat(user, session.id, adapter, prepared["is_new"], payload.get("message")))
    _background.add(task)
    task.add_done_callback(_background.discard)

    yield {"event": "done", "data": {"session_id": session.id,
                                     "thinking_time_ms": int((time.monotonic() - started) * 1000)}}


# ---------------------------------------------------------------- 后台任务：标题与摘要

async def _after_chat(user, session_id: int, adapter, is_new: bool, first_message: str | None):
    try:
        if is_new and first_message:
            await _generate_title(session_id, first_message, adapter)
        await _compress_if_needed(session_id, adapter)
    except Exception:
        logger.warning("会话 %s 的后台任务失败", session_id, exc_info=True)


async def _complete_text(adapter, system: str, user_text: str) -> str:
    response = await adapter.chat([{"role": "system", "content": system},
                                   {"role": "user", "content": user_text}], [])
    return (response.content or "").strip()


async def _generate_title(session_id: int, first_message: str, adapter):
    title = await _complete_text(
        adapter, "根据用户的第一条消息，生成一个简短的对话标题（10字以内）。只返回标题文字，不要加引号或其他标点。",
        first_message)
    title = title.strip("\"'“”‘’「」《》 \n")[:50]
    if title:
        await sync_to_async(ChatSession.objects.filter(id=session_id, title__isnull=True).update)(title=title)


def _summary_input(session_id: int):
    """返回 (已有摘要, 待压缩的文本, 压缩覆盖到的 seq_num)；不需要压缩时返回 None。"""
    session = ChatSession.objects.get(id=session_id)
    pending = list(sessions.unsummarized_messages(session))
    if len(pending) < SUMMARY_THRESHOLD or len(pending) <= SUMMARY_KEEP_RECENT:
        return None
    to_compress = pending[:-SUMMARY_KEEP_RECENT]
    lines = []
    for m in to_compress:
        if m.role == "tool":
            lines.append(f"[工具 {m.tool_name}: {json.dumps(m.tool_result, ensure_ascii=False)[:200]}]")
        else:
            lines.append(f"{m.role}: {(m.content or '[无文本]')[:300]}")
    return session.summary, "\n".join(lines), to_compress[-1].seq_num


async def _compress_if_needed(session_id: int, adapter):
    found = await sync_to_async(_summary_input)(session_id)
    if found is None:
        return
    old_summary, text, up_to = found
    prefix = f"之前的摘要：{old_summary}\n\n" if old_summary else ""
    summary = await _complete_text(
        adapter,
        "请将以下对话内容压缩为一段 200 字以内的摘要。保留关键信息（涉及的金额、日期、操作结果等），"
        "去掉不重要的细节。只返回摘要文字。",
        f"{prefix}需要压缩的对话：\n{text}")
    if summary:
        await sync_to_async(ChatSession.objects.filter(id=session_id).update)(summary=summary, summary_up_to=up_to)
        logger.info("会话 %s 摘要完成，覆盖到 seq_num=%s", session_id, up_to)


# ---------------------------------------------------------------- 对外接口

async def _send(user, payload: dict) -> dict:
    session_id, content, tool_results = None, "", []
    async for ev in _run(user, payload, streaming=False):
        data = ev["data"]
        if ev["event"] == "session_created":
            session_id = data["session_id"]
        elif ev["event"] == "thinking":
            content = ""  # 只返回最后一轮的回复，前面几轮是工具调用的铺垫
        elif ev["event"] == "text_delta":
            content += data["content"]
        elif ev["event"] == "tool_result":
            tool_results.append(data)
    return {"session_id": session_id, "content": content, "tool_results": tool_results}


def send(user, payload: dict) -> dict:
    """非流式对话，返回 {session_id, content, tool_results}。"""
    try:
        return async_to_sync(_send)(user, payload)
    except BusinessError:
        raise
    except Exception as exc:
        logger.warning("AI 调用失败", exc_info=True)
        raise BusinessError(f"AI 服务调用失败: {exc}", status=502) from exc


async def stream(user, payload: dict) -> AsyncIterator[dict]:
    """流式对话，逐个 yield {"event": ..., "data": {...}}。出错时推送 error 事件而不是中断连接。"""
    try:
        async for event in _run(user, payload, streaming=True):
            yield event
    except BusinessError as exc:
        yield {"event": "error", "data": {"message": exc.message}}
    except Exception as exc:
        logger.warning("AI 流式调用失败", exc_info=True)
        yield {"event": "error", "data": {"message": f"AI 服务调用失败: {exc}"}}
