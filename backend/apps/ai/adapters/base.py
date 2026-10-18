"""
AI 适配器抽象。对应原项目 ai/adapters/base.adapter.ts 与 ai/types/chat.types.ts。

统一消息格式（各适配器负责与厂商格式互转）：
    {"role": "user" | "assistant" | "tool" | "system",
     "content": str | [{"type": "text", "text": ...}, {"type": "image", "data": base64, "media_type": ...}],
     "tool_calls": [{"id", "name", "arguments": dict}],   # assistant 消息
     "tool_call_id": str, "tool_name": str, "tool_result": dict}   # tool 消息

流式事件（chat_stream 逐个 yield）：
    {"type": "text_delta", "content": str}
    {"type": "thinking_delta", "content": str}
    {"type": "tool_call_start", "tool_call_id": str, "tool_name": str}
    {"type": "tool_call_delta", "tool_call_id": str, "arguments_delta": str}
    {"type": "tool_call_end", "tool_call_id": str, "arguments": dict}
    {"type": "done", "stop_reason": "end_turn" | "tool_use" | "max_tokens", "usage": dict | None}
"""
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterConfig:
    api_key: str
    model: str
    api_base_url: str | None = None
    http_client: Any = None  # 可注入 httpx.AsyncClient（测试时用 MockTransport）


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ChatResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str | None = None
    usage: dict | None = None


class AIAdapter(ABC):
    provider: str = ""

    def __init__(self, config: AdapterConfig):
        self.config = config

    @abstractmethod
    async def test_connection(self) -> bool:
        """发一条极短的请求，验证 Key / 地址 / 模型是否可用。"""

    @abstractmethod
    async def chat(self, messages: list[dict], tools: list[dict]) -> ChatResponse:
        """多轮对话（支持 Tool Use），同步返回完整结果。"""

    @abstractmethod
    def chat_stream(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[dict]:
        """多轮对话（支持 Tool Use），流式返回事件，格式见模块文档。"""


def split_data_url(data: str, default_media_type: str = "image/jpeg") -> tuple[str, str]:
    """图片可能是纯 Base64，也可能是 data:image/png;base64,... ，统一拆成 (media_type, base64)。"""
    if data.startswith("data:") and ";base64," in data:
        header, _, payload = data.partition(";base64,")
        return header[5:] or default_media_type, payload
    return default_media_type, data


def tool_result_text(msg: dict) -> str:
    return json.dumps(msg.get("tool_result"), ensure_ascii=False, default=str)


def text_of(content) -> str:
    """取出消息中的纯文本部分。"""
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content or [] if b.get("type") == "text")
