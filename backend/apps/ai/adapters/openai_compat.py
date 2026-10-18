"""
OpenAI 兼容适配器：OpenAI / DeepSeek / Qwen 共用，差异只在默认 base_url 与少量参数。
参考原项目 openai.adapter.ts / deepseek.adapter.ts / qwen.adapter.ts / openai-compatible.helper.ts。
"""
from openai import AsyncOpenAI

from .base import AIAdapter, ChatResponse

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


class OpenAICompatAdapter(AIAdapter):
    def __init__(self, config, provider="openai"):
        super().__init__(config)
        self.provider = provider

    def _client(self):
        return AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base_url or DEFAULT_BASE_URLS[self.provider],
        )

    async def test_connection(self) -> bool:
        await self._client().chat.completions.create(
            model=self.config.model, max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True

    async def chat(self, messages, tools) -> ChatResponse:
        # TODO: 1. 统一格式 → OpenAI 格式（图片转 image_url data URI，tool_calls.arguments 转 JSON 字符串）
        #       2. tools → [{"type": "function", "function": {"name", "description", "parameters"}}]
        #       3. 解析 choices[0].message 为 ChatResponse
        raise NotImplementedError

    async def chat_stream(self, messages, tools):
        # TODO: stream=True，按 delta.content / delta.tool_calls[index] 累积并转换为统一流式事件；
        #       DeepSeek 推理模型的 reasoning_content 转为 thinking_delta
        raise NotImplementedError
        yield  # noqa: 使其成为异步生成器
