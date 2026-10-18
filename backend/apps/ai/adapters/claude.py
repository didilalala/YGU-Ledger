"""
Claude 适配器，基于官方 anthropic SDK。
参考原项目 ai/adapters/claude.adapter.ts（消息格式转换、tool_use / tool_result 块、流式事件解析）。
"""
from anthropic import AsyncAnthropic

from .base import AIAdapter, ChatResponse, ToolCall, split_data_url, text_of, tool_result_text

MAX_TOKENS = 4096


class ClaudeAdapter(AIAdapter):
    provider = "claude"

    def _client(self):
        return AsyncAnthropic(api_key=self.config.api_key, base_url=self.config.api_base_url or None,
                              http_client=self.config.http_client)

    async def test_connection(self) -> bool:
        await self._client().messages.create(
            model=self.config.model, max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True

    # ---------- 格式转换 ----------

    @staticmethod
    def _user_content(content):
        if isinstance(content, str):
            return content
        blocks = []
        for b in content or []:
            if b["type"] == "image":
                media_type, data = split_data_url(b["data"], b.get("media_type", "image/jpeg"))
                blocks.append({"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}})
            else:
                blocks.append({"type": "text", "text": b["text"]})
        return blocks

    def _translate(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """统一格式 → (system 文本, Anthropic messages)。"""
        system = "\n\n".join(text_of(m["content"]) for m in messages if m["role"] == "system")
        result: list[dict] = []
        for m in messages:
            role = m["role"]
            if role == "user":
                result.append({"role": "user", "content": self._user_content(m["content"])})
            elif role == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": text_of(m["content"])})
                for tc in m.get("tool_calls") or []:
                    blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["arguments"]})
                if blocks:
                    result.append({"role": "assistant", "content": blocks})
            elif role == "tool":
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": tool_result_text(m)}
                # 同一轮的多个工具结果合并到一条 user 消息里（Anthropic 要求 tool_result 紧跟在 tool_use 之后）
                last = result[-1] if result else None
                if last and last["role"] == "user" and isinstance(last["content"], list) \
                        and last["content"] and last["content"][0]["type"] == "tool_result":
                    last["content"].append(block)
                else:
                    result.append({"role": "user", "content": [block]})
        return system, result

    @staticmethod
    def _tools(tools: list[dict]):
        return [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
                for t in tools]

    def _params(self, messages, tools) -> dict:
        system, converted = self._translate(messages)
        params = {"model": self.config.model, "max_tokens": MAX_TOKENS, "messages": converted}
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self._tools(tools)
        return params

    @staticmethod
    def _stop_reason(value) -> str:
        return value if value in ("tool_use", "max_tokens") else "end_turn"

    # ---------- 调用 ----------

    async def chat(self, messages, tools) -> ChatResponse:
        resp = await self._client().messages.create(**self._params(messages, tools))
        text, calls = "", []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input or {}))
        usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
        return ChatResponse(content=text or None, tool_calls=calls,
                            stop_reason=self._stop_reason(resp.stop_reason), usage=usage)

    async def chat_stream(self, messages, tools):
        stream = await self._client().messages.create(**self._params(messages, tools), stream=True)
        tool_id = None
        async for ev in stream:
            if ev.type == "content_block_start":
                if ev.content_block.type == "tool_use":
                    tool_id = ev.content_block.id
                    yield {"type": "tool_call_start", "tool_call_id": tool_id,
                           "tool_name": ev.content_block.name}
            elif ev.type == "content_block_delta":
                if ev.delta.type == "text_delta" and ev.delta.text:
                    yield {"type": "text_delta", "content": ev.delta.text}
                elif ev.delta.type == "thinking_delta" and ev.delta.thinking:
                    yield {"type": "thinking_delta", "content": ev.delta.thinking}
                elif ev.delta.type == "input_json_delta" and ev.delta.partial_json:
                    yield {"type": "tool_call_delta", "tool_call_id": tool_id,
                           "arguments_delta": ev.delta.partial_json}
            elif ev.type == "content_block_stop":
                if tool_id:
                    yield {"type": "tool_call_end", "tool_call_id": tool_id}
                    tool_id = None
            elif ev.type == "message_delta":
                usage = getattr(ev, "usage", None)
                yield {"type": "done", "stop_reason": self._stop_reason(ev.delta.stop_reason),
                       "usage": {"output_tokens": usage.output_tokens} if usage else None}
