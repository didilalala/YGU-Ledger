"""
Claude 适配器，基于官方 anthropic SDK。
参考原项目 ai/adapters/claude.adapter.ts（消息格式转换、tool_use / tool_result 块、流式事件解析）。
"""
from anthropic import AsyncAnthropic

from .base import AIAdapter, ChatResponse


class ClaudeAdapter(AIAdapter):
    provider = "claude"

    def _client(self):
        return AsyncAnthropic(api_key=self.config.api_key, base_url=self.config.api_base_url or None)

    async def test_connection(self) -> bool:
        await self._client().messages.create(
            model=self.config.model, max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True

    async def chat(self, messages, tools) -> ChatResponse:
        # TODO: 1. 抽出 system 消息作为 system 参数
        #       2. 统一格式 → Anthropic 格式（tool 消息转为 user 角色的 tool_result 块，图片转 image 块）
        #       3. tools → [{"name", "description", "input_schema"}]
        #       4. 解析响应中的 text / tool_use 块为 ChatResponse
        raise NotImplementedError

    async def chat_stream(self, messages, tools):
        # TODO: 使用 client.messages.stream(...)，把 content_block_start / delta / stop
        #       转换为 base.py 中定义的统一流式事件
        raise NotImplementedError
        yield  # noqa: 使其成为异步生成器
