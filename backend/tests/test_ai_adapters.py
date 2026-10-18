"""适配器测试：用 httpx.MockTransport 喂真实格式的响应，不访问外网。"""
import asyncio
import json

import httpx
import httpx2  # anthropic SDK 自带的 HTTP 库，与 httpx 的对象不通用

from apps.ai.adapters import AdapterConfig, ClaudeAdapter, OpenAICompatAdapter
from apps.ai.tools import TOOLS


def run(coro):
    return asyncio.run(coro)


def make(adapter_cls, handler, **kwargs):
    lib = httpx2 if adapter_cls is ClaudeAdapter else httpx
    client = lib.AsyncClient(transport=lib.MockTransport(handler))
    return adapter_cls(AdapterConfig(api_key="k", model="m", http_client=client), **kwargs)


def sse(*events, lib=httpx):
    """events: (event_name | None, payload dict) → SSE 响应"""
    out = ""
    for name, payload in events:
        out += (f"event: {name}\n" if name else "") + f"data: {json.dumps(payload)}\n\n"
    return lib.Response(200, headers={"content-type": "text/event-stream"}, content=out.encode())


HISTORY = [
    {"role": "system", "content": "SYS"},
    {"role": "user", "content": [{"type": "text", "text": "看图"},
                                 {"type": "image", "data": "data:image/png;base64,AAAA"}]},
    {"role": "assistant", "content": "好的", "tool_calls": [
        {"id": "c1", "name": "query_bills", "arguments": {"limit": 5}},
        {"id": "c2", "name": "get_statistics", "arguments": {}}]},
    {"role": "tool", "tool_call_id": "c1", "tool_name": "query_bills", "tool_result": {"success": True, "msg": "中"}},
    {"role": "tool", "tool_call_id": "c2", "tool_name": "get_statistics", "tool_result": {"success": True}},
]


# ---------------------------------------------------------------- Claude

def test_claude_request_translation():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        seen["path"] = request.url.path
        return httpx2.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "m", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "你好"}],
            "usage": {"input_tokens": 3, "output_tokens": 2}})

    resp = run(make(ClaudeAdapter, handler).chat(HISTORY, TOOLS))
    assert resp.content == "你好" and resp.stop_reason == "end_turn" and resp.usage["output_tokens"] == 2
    assert seen["path"] == "/v1/messages"
    assert seen["system"] == "SYS"
    assert seen["tools"][0]["input_schema"]["type"] == "object"
    user, assistant, results = seen["messages"]
    # data URL 被拆成 media_type + 纯 base64
    assert user["content"][1]["source"] == {"type": "base64", "media_type": "image/png", "data": "AAAA"}
    assert [b["type"] for b in assistant["content"]] == ["text", "tool_use", "tool_use"]
    assert assistant["content"][1]["input"] == {"limit": 5}
    # 同一轮的两个工具结果合并成一条 user 消息
    assert [b["tool_use_id"] for b in results["content"]] == ["c1", "c2"]
    assert "中" in results["content"][0]["content"]  # 中文不被转义


def test_claude_chat_parses_tool_use():
    def handler(request):
        return httpx2.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "m", "stop_reason": "tool_use",
            "content": [{"type": "text", "text": "记一下"},
                        {"type": "tool_use", "id": "t1", "name": "create_bills", "input": {"bills": []}}],
            "usage": {"input_tokens": 1, "output_tokens": 1}})

    resp = run(make(ClaudeAdapter, handler).chat([{"role": "user", "content": "x"}], TOOLS))
    assert resp.stop_reason == "tool_use"
    assert (resp.tool_calls[0].id, resp.tool_calls[0].name) == ("t1", "create_bills")


def test_claude_stream_events():
    def handler(request):
        assert json.loads(request.content)["stream"] is True
        return sse(
            ("message_start", {"type": "message_start", "message": {
                "id": "m", "type": "message", "role": "assistant", "model": "m", "content": [],
                "usage": {"input_tokens": 1, "output_tokens": 0}}}),
            ("content_block_start", {"type": "content_block_start", "index": 0,
                                     "content_block": {"type": "text", "text": ""}}),
            ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                     "delta": {"type": "text_delta", "text": "记"}}),
            ("content_block_stop", {"type": "content_block_stop", "index": 0}),
            ("content_block_start", {"type": "content_block_start", "index": 1, "content_block": {
                "type": "tool_use", "id": "t1", "name": "create_bills", "input": {}}}),
            ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                     "delta": {"type": "input_json_delta", "partial_json": '{"bills"'}}),
            ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                     "delta": {"type": "input_json_delta", "partial_json": ": []}"}}),
            ("content_block_stop", {"type": "content_block_stop", "index": 1}),
            ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "tool_use"},
                               "usage": {"output_tokens": 9}}),
            ("message_stop", {"type": "message_stop"}),
            lib=httpx2,
        )

    async def collect():
        return [e async for e in make(ClaudeAdapter, handler).chat_stream([{"role": "user", "content": "x"}], TOOLS)]

    events = run(collect())
    assert events == [
        {"type": "text_delta", "content": "记"},
        {"type": "tool_call_start", "tool_call_id": "t1", "tool_name": "create_bills"},
        {"type": "tool_call_delta", "tool_call_id": "t1", "arguments_delta": '{"bills"'},
        {"type": "tool_call_delta", "tool_call_id": "t1", "arguments_delta": ": []}"},
        {"type": "tool_call_end", "tool_call_id": "t1"},
        {"type": "done", "stop_reason": "tool_use", "usage": {"output_tokens": 9}},
    ]


# ---------------------------------------------------------------- OpenAI 兼容

def test_openai_request_translation():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        seen["url"] = str(request.url)
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 1, "model": "m",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [
                    {"id": "t1", "type": "function",
                     "function": {"name": "query_bills", "arguments": '{"limit": 3}'}}]}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 5, "total_tokens": 9}})

    resp = run(make(OpenAICompatAdapter, handler, provider="deepseek").chat(HISTORY, TOOLS))
    assert seen["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert seen["parallel_tool_calls"] is False and seen["tools"][0]["type"] == "function"
    system, user, assistant, *tool_msgs = seen["messages"]
    assert system == {"role": "system", "content": "SYS"}
    assert user["content"][1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    assert json.loads(assistant["tool_calls"][0]["function"]["arguments"]) == {"limit": 5}
    assert [m["tool_call_id"] for m in tool_msgs] == ["c1", "c2"]
    assert resp.stop_reason == "tool_use" and resp.tool_calls[0].arguments == {"limit": 3}


def test_openai_bad_tool_arguments_become_empty_dict():
    def handler(request):
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 1, "model": "m",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [
                    {"id": "t1", "type": "function", "function": {"name": "x", "arguments": "{oops"}}]}}]})

    resp = run(make(OpenAICompatAdapter, handler).chat([{"role": "user", "content": "x"}], TOOLS))
    assert resp.tool_calls[0].arguments == {}


def test_openai_reasoner_gets_reasoning_content():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"id": "c", "object": "chat.completion", "created": 1, "model": "m",
                                         "choices": [{"index": 0, "finish_reason": "stop",
                                                      "message": {"role": "assistant", "content": "ok"}}]})

    adapter = OpenAICompatAdapter(AdapterConfig(
        api_key="k", model="deepseek-reasoner",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))), provider="deepseek")
    run(adapter.chat([{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"},
                      {"role": "user", "content": "z"}], []))
    assert seen["messages"][1]["reasoning_content"] == ""
    assert "tools" not in seen


def chunk(delta, finish=None):
    return (None, {"id": "c", "object": "chat.completion.chunk", "created": 1, "model": "m",
                   "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]})


def test_openai_stream_text_reasoning_and_tool_calls():
    def handler(request):
        return sse(
            chunk({"role": "assistant", "reasoning_content": "想想"}),
            chunk({"content": "好"}),
            chunk({"tool_calls": [{"index": 0, "id": "t1", "type": "function",
                                   "function": {"name": "create_bills", "arguments": ""}}]}),
            chunk({"tool_calls": [{"index": 0, "function": {"arguments": '{"bills"'}}]}),
            chunk({"tool_calls": [{"index": 0, "function": {"arguments": ": []}"}}]}),
            chunk({}, finish="tool_calls"),
        )

    async def collect():
        adapter = make(OpenAICompatAdapter, handler, provider="qwen")
        return [e async for e in adapter.chat_stream([{"role": "user", "content": "x"}], TOOLS)]

    assert run(collect()) == [
        {"type": "thinking_delta", "content": "想想"},
        {"type": "text_delta", "content": "好"},
        {"type": "tool_call_start", "tool_call_id": "t1", "tool_name": "create_bills"},
        {"type": "tool_call_delta", "tool_call_id": "t1", "arguments_delta": '{"bills"'},
        {"type": "tool_call_delta", "tool_call_id": "t1", "arguments_delta": ": []}"},
        {"type": "tool_call_end", "tool_call_id": "t1"},
        {"type": "done", "stop_reason": "tool_use", "usage": None},
    ]


def test_openai_stream_name_arrives_in_later_chunk():
    def handler(request):
        return sse(
            chunk({"tool_calls": [{"index": 0, "id": "t1", "type": "function", "function": {"arguments": ""}}]}),
            chunk({"tool_calls": [{"index": 0, "function": {"name": "get_statistics", "arguments": "{}"}}]}),
            chunk({}, finish="stop"),
        )

    async def collect():
        return [e async for e in make(OpenAICompatAdapter, handler).chat_stream([{"role": "user", "content": "x"}], TOOLS)]

    events = run(collect())
    assert events[0] == {"type": "tool_call_start", "tool_call_id": "t1", "tool_name": "get_statistics"}
    assert events[-1]["stop_reason"] == "end_turn"  # 厂商返回 stop，编排层靠工具调用本身判断
