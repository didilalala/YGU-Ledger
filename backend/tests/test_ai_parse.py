"""旧接口 /api/ai/parse-bills 与模型回复的解析。"""
from datetime import date

import pytest

from apps.ai.adapters import ChatResponse
from apps.ai.models import AIModelConfig
from apps.ai.services import parse
from apps.ai.services.parse import parse_ai_response


# ---------------------------------------------------------------- 回复解析

def test_parse_valid_array():
    text = '[{"amount": 25.6, "type": "expense", "categoryName": "餐饮", "description": "咖啡", "date": "2026-10-01"}]'
    assert parse_ai_response(text) == [{"amount": 25.6, "type": "expense", "category_name": "餐饮",
                                        "description": "咖啡", "date": "2026-10-01"}]


def test_parse_extracts_array_from_chatty_reply_and_code_fence():
    text = '好的，识别结果如下：\n```json\n[{"amount": 8, "type": "income", "categoryName": "工资", "description": "奖金", "date": "2026-10-02"}]\n```'
    assert [b["amount"] for b in parse_ai_response(text)] == [8.0]


def test_parse_description_containing_bracket_is_not_truncated():
    text = '[{"amount": 5, "type": "expense", "categoryName": "餐饮", "description": "奶茶[大杯]", "date": "2026-10-02"}]'
    assert parse_ai_response(text)[0]["description"] == "奶茶[大杯]"


@pytest.mark.parametrize("text", ["", "没有账单", "[]", "[oops", '{"amount": 1}', "[1, 2, 3]", None])
def test_parse_garbage_returns_empty(text):
    assert parse_ai_response(text) == []


def test_parse_drops_invalid_items_and_fixes_bad_dates():
    base = {"type": "expense", "categoryName": "餐饮", "description": "x", "date": "2026-10-01"}
    items = [
        {**base, "amount": 10},                       # 合法
        {**base, "amount": -5},                       # 负数
        {**base, "amount": 0},                        # 0
        {**base, "amount": "12"},                     # 字符串金额
        {**base, "amount": True},                     # 布尔值不是金额
        {**base, "amount": 5, "type": "transfer"},    # 类型不对
        {**base, "amount": 5, "categoryName": None},  # 缺分类
        {**base, "amount": 7, "date": "昨天"},          # 日期不合法 → 今天
        {**base, "amount": 1.239, "description": "长" * 300},  # 金额取两位，描述截到 100
    ]
    import json

    bills = parse_ai_response(json.dumps(items))
    assert [b["amount"] for b in bills] == [10.0, 7.0, 1.24]
    assert bills[1]["date"] == date.today().isoformat()
    assert len(bills[2]["description"]) == 100


# ---------------------------------------------------------------- 接口

REPLY = '[{"amount": 32, "type": "expense", "categoryName": "餐饮", "description": "午饭", "date": "2026-10-18"}]'


class FakeAdapter:
    def __init__(self, reply=REPLY, error=None):
        self.reply, self.error, self.calls = reply, error, []

    async def chat(self, messages, tools):
        self.calls.append((messages, tools))
        if self.error:
            raise self.error
        return ChatResponse(content=self.reply)


@pytest.fixture
def config(user):
    return AIModelConfig.objects.create(user=user, name="t", provider="openai", api_key="k", model="m",
                                        is_default=True, supports_vision=False)


def use(monkeypatch, adapter):
    monkeypatch.setattr(parse, "get_adapter", lambda cfg: adapter)
    return adapter


def test_parse_text_endpoint(client, config, monkeypatch):
    adapter = use(monkeypatch, FakeAdapter())
    resp = client.post("/api/ai/parse-bills", {"type": "text", "content": "中午吃饭 32"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["bills"] == [{"amount": 32.0, "type": "expense", "categoryName": "餐饮",
                                              "description": "午饭", "date": "2026-10-18"}]
    messages, tools = adapter.calls[0]
    assert tools == [] and "中午吃饭 32" in messages[0]["content"] and "JSON 数组" in messages[0]["content"]


def test_parse_image_requires_vision_model(client, config, monkeypatch):
    use(monkeypatch, FakeAdapter())
    resp = client.post("/api/ai/parse-bills", {"type": "image", "content": "QUJD"}, format="json")
    assert resp.status_code == 400 and resp.json()["message"] == "当前模型不支持图片识别"

    config.supports_vision = True
    config.save()
    adapter = use(monkeypatch, FakeAdapter())
    resp = client.post("/api/ai/parse-bills", {"type": "image", "content": "QUJD"}, format="json")
    assert resp.status_code == 200
    blocks = adapter.calls[0][0][0]["content"]
    assert [b["type"] for b in blocks] == ["image", "text"] and blocks[0]["data"] == "QUJD"


def test_parse_uses_explicit_config_and_rejects_foreign_one(client, config, other_client, monkeypatch):
    from apps.users.models import User

    use(monkeypatch, FakeAdapter())
    foreign = AIModelConfig.objects.create(user=User.objects.get(username="bob"), name="x", provider="openai",
                                           api_key="k", model="m")
    resp = client.post("/api/ai/parse-bills", {"type": "text", "content": "x", "configId": foreign.id}, format="json")
    assert resp.status_code == 404


def test_parse_without_config_provider_error_and_validation(client, monkeypatch):
    resp = client.post("/api/ai/parse-bills", {"type": "text", "content": "x"}, format="json")
    assert resp.status_code == 400 and resp.json()["message"] == "请先配置 AI 模型"

    assert client.post("/api/ai/parse-bills", {"type": "video", "content": "x"}, format="json").status_code == 400
    assert client.post("/api/ai/parse-bills", {"type": "text"}, format="json").status_code == 400


def test_parse_provider_failure_is_502(client, config, monkeypatch):
    use(monkeypatch, FakeAdapter(error=RuntimeError("upstream down")))
    resp = client.post("/api/ai/parse-bills", {"type": "text", "content": "x"}, format="json")
    assert resp.status_code == 502 and "upstream down" in resp.json()["message"]


def test_parse_unrecognizable_reply_gives_empty_list(client, config, monkeypatch):
    use(monkeypatch, FakeAdapter(reply="抱歉，我没看到账单"))
    resp = client.post("/api/ai/parse-bills", {"type": "text", "content": "你好"}, format="json")
    assert resp.status_code == 200 and resp.json()["data"]["bills"] == []
