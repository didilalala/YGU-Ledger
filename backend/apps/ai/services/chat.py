"""
对话编排。对应原项目 ai/services/chat.service.ts（约 750 行，迁移重点）。

一次对话的流程：
  1. 取会话（没有则创建，流式时先推送 session_created 事件）
  2. 保存用户消息（含图片）
  3. build_context() 组装上下文 + 系统提示词
  4. 调用适配器；若返回 tool_calls：
       保存 assistant 消息 → 逐个 tool_executor.execute() → 保存 tool 消息 → 再次调用适配器
     循环直到没有 tool_calls 或达到 MAX_TOOL_ROUNDS
  5. 保存最终 assistant 回复；首轮对话自动生成会话标题

流式事件（推送给前端，SSE `data: {"event": ..., "data": {...}}`）：
  session_created / thinking / thinking_delta / text_delta / tool_call_start / tool_result / done / error
"""
from collections.abc import AsyncIterator

MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = (
    "你是 LiteNote 的记账助手。用户描述消费或收入时，调用 create_bills 记账；"
    "询问账单或统计时，调用 query_bills / get_statistics。今天是 {today}。"
)


def send(user, payload: dict) -> dict:
    """非流式对话，返回 {session_id, content, tool_results}。"""
    # TODO: 按模块文档实现
    raise NotImplementedError


async def stream(user, payload: dict) -> AsyncIterator[dict]:
    """流式对话，逐个 yield {"event": ..., "data": {...}}。"""
    # TODO: 按模块文档实现；数据库操作在异步上下文中需用 sync_to_async 包装
    yield {"event": "error", "data": {"message": "流式对话尚未实现"}}
