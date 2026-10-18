from .base import AdapterConfig, AIAdapter, ChatResponse, ToolCall
from .claude import ClaudeAdapter
from .openai_compat import OpenAICompatAdapter


def get_adapter(ai_config) -> AIAdapter:
    """根据 AIModelConfig 返回对应适配器。"""
    config = AdapterConfig(api_key=ai_config.api_key, model=ai_config.model,
                           api_base_url=ai_config.api_base_url)
    if ai_config.provider == "claude":
        return ClaudeAdapter(config)
    if ai_config.provider in ("openai", "deepseek", "qwen"):
        return OpenAICompatAdapter(config, provider=ai_config.provider)
    raise ValueError(f"不支持的服务商: {ai_config.provider}")


__all__ = ["AdapterConfig", "AIAdapter", "ChatResponse", "ToolCall", "get_adapter"]
