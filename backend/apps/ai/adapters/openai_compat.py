"""
OpenAI 兼容适配器：OpenAI / DeepSeek / Qwen 共用，差异只在默认 base_url 与少量参数。
参考原项目 openai.adapter.ts / deepseek.adapter.ts / qwen.adapter.ts / openai-compatible.helper.ts。
"""
import json

from openai import AsyncOpenAI

from .base import AIAdapter, ChatResponse, ToolCall, split_data_url, text_of, tool_result_text

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}
MAX_TOKENS = 4096


def _stop_reason(finish_reason) -> str:
    if finish_reason in ("tool_calls", "function_call"):
        return "tool_use"
    if finish_reason == "length":
        return "max_tokens"
    return "end_turn"


def _parse_arguments(raw: str | None) -> dict:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


class OpenAICompatAdapter(AIAdapter):
    def __init__(self, config, provider="openai"):
        super().__init__(config)
        self.provider = provider

    def _client(self):
        return AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base_url or DEFAULT_BASE_URLS[self.provider],
            http_client=self.config.http_client,
        )

    async def test_connection(self) -> bool:
        await self._client().chat.completions.create(
            model=self.config.model, max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True

    # ---------- 格式转换 ----------

    @staticmethod
    def _user_content(content):
        if isinstance(content, str):
            return content
        parts = []
        for b in content or []:
            if b["type"] == "image":
                media_type, data = split_data_url(b["data"], b.get("media_type", "image/jpeg"))
                parts.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}})
            else:
                parts.append({"type": "text", "text": b["text"]})
        return parts

    def _translate(self, messages: list[dict]) -> list[dict]:
        result = []
        for m in messages:
            role = m["role"]
            if role == "system":
                result.append({"role": "system", "content": text_of(m["content"])})
            elif role == "user":
                result.append({"role": "user", "content": self._user_content(m["content"])})
            elif role == "assistant":
                item = {"role": "assistant", "content": text_of(m["content"]) if m.get("content") else None}
                if m.get("tool_calls"):
                    item["tool_calls"] = [
                        {"id": tc["id"], "type": "function",
                         "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"], ensure_ascii=False)}}
                        for tc in m["tool_calls"]
                    ]
                result.append(item)
            elif role == "tool":
                result.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": tool_result_text(m)})
        # DeepSeek 推理模型要求历史 assistant 消息都带 reasoning_content
        if "reasoner" in (self.config.model or ""):
            for item in result:
                if item["role"] == "assistant":
                    item.setdefault("reasoning_content", "")
        return result

    def _params(self, messages, tools) -> dict:
        params = {"model": self.config.model, "max_tokens": MAX_TOKENS, "messages": self._translate(messages)}
        if tools:
            params["tools"] = [{"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in tools]
            params["parallel_tool_calls"] = False
        return params

    # ---------- 调用 ----------

    async def chat(self, messages, tools) -> ChatResponse:
        resp = await self._client().chat.completions.create(**self._params(messages, tools))
        if not resp.choices:
            return ChatResponse(content=None, stop_reason="end_turn")
        choice = resp.choices[0]
        calls = [ToolCall(id=tc.id, name=tc.function.name, arguments=_parse_arguments(tc.function.arguments))
                 for tc in choice.message.tool_calls or []]
        usage = {"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens} \
            if resp.usage else None
        return ChatResponse(content=choice.message.content or None, tool_calls=calls,
                            stop_reason=_stop_reason(choice.finish_reason), usage=usage)

    async def chat_stream(self, messages, tools):
        stream = await self._client().chat.completions.create(
            **self._params(messages, tools), stream=True)
        calls: dict[int, dict] = {}  # index → {id, name, started}
        finish = None
        usage = None
        async for chunk in stream:
            if chunk.usage:
                usage = {"input_tokens": chunk.usage.prompt_tokens, "output_tokens": chunk.usage.completion_tokens}
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta
            if delta.content:
                yield {"type": "text_delta", "content": delta.content}
            # 思维链字段：DeepSeek 用 reasoning_content，部分厂商用 reasoning（SDK 把未知字段放在属性上）
            reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
            if reasoning:
                yield {"type": "thinking_delta", "content": reasoning}
            for tc in delta.tool_calls or []:
                info = calls.setdefault(tc.index or 0, {"id": None, "name": "", "started": False})
                if tc.id and not info["id"]:
                    info["id"] = tc.id
                if tc.function and tc.function.name and not info["name"]:
                    info["name"] = tc.function.name
                # id 和名称都到齐才通知前端（部分兼容厂商把名称放在后续分片里）
                if info["id"] and info["name"] and not info["started"]:
                    info["started"] = True
                    yield {"type": "tool_call_start", "tool_call_id": info["id"], "tool_name": info["name"]}
                if tc.function and tc.function.arguments and info["id"]:
                    yield {"type": "tool_call_delta", "tool_call_id": info["id"],
                           "arguments_delta": tc.function.arguments}
            if choice.finish_reason:
                finish = choice.finish_reason
        for info in calls.values():
            if info["started"]:
                yield {"type": "tool_call_end", "tool_call_id": info["id"]}
        yield {"type": "done", "stop_reason": _stop_reason(finish), "usage": usage}
