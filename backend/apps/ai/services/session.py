"""
会话与消息持久化。对应原项目 ai/services/session.service.ts。
"""
import json

from django.db import transaction
from django.db.models import Max

from ..models import ChatMessage, ChatSession

MAX_CONTEXT_MESSAGES = 30


def create_session(user, ai_config=None, title=None) -> ChatSession:
    return ChatSession.objects.create(user=user, ai_config=ai_config, title=title)


@transaction.atomic
def append_message(session: ChatSession, role: str, **fields) -> ChatMessage:
    """追加一条消息，seq_num 在会话内递增。"""
    # 锁住会话行，避免并发写入产生重复 seq_num
    ChatSession.objects.select_for_update().filter(pk=session.pk).first()
    last = session.messages.aggregate(m=Max("seq_num"))["m"] or 0
    msg = ChatMessage.objects.create(session=session, seq_num=last + 1, role=role, **fields)
    session.save(update_fields=["updated_at"])
    return msg


def unsummarized_messages(session: ChatSession):
    qs = session.messages.all()
    if session.summary_up_to:
        qs = qs.filter(seq_num__gt=session.summary_up_to)
    return qs.order_by("seq_num")


def _images_of(msg: ChatMessage) -> list[str]:
    """image_url 列内是 JSON 数组；兼容早期直接存单个字符串的数据。"""
    if not msg.image_url:
        return []
    try:
        parsed = json.loads(msg.image_url)
    except ValueError:
        return [msg.image_url]
    return parsed if isinstance(parsed, list) else [msg.image_url]


def to_unified(msg: ChatMessage) -> dict:
    """数据库消息 → adapters/base.py 中的统一消息格式。"""
    if msg.role == "user":
        images = _images_of(msg)
        if not images:
            return {"role": "user", "content": msg.content or ""}
        blocks = [{"type": "text", "text": msg.content}] if msg.content else []
        blocks += [{"type": "image", "data": data, "media_type": "image/jpeg"} for data in images]
        return {"role": "user", "content": blocks}
    if msg.role == "assistant":
        item = {"role": "assistant", "content": msg.content or None}
        if msg.tool_calls:
            item["tool_calls"] = msg.tool_calls
        return item
    if msg.role == "tool":
        return {"role": "tool", "tool_call_id": msg.tool_call_id, "tool_name": msg.tool_name,
                "tool_result": msg.tool_result}
    return {"role": msg.role, "content": msg.content or ""}


def sanitize(messages: list[dict]) -> list[dict]:
    """
    保证历史对 API 合法：
    - 第一条必须是 user（裁剪上下文可能切在工具调用中间）；
    - assistant 的 tool_calls 必须都有对应的 tool 结果（流被中断时可能缺失），否则去掉 tool_calls；
    - 没有对应 tool_calls 的 tool 消息直接丢弃。
    """
    while messages and messages[0]["role"] != "user":
        messages = messages[1:]

    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    result, open_ids = [], set()
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            if all(tc["id"] in answered for tc in m["tool_calls"]):
                open_ids |= {tc["id"] for tc in m["tool_calls"]}
            else:
                m = {**m, "tool_calls": None}
                if not m["content"]:
                    continue
        elif m["role"] == "tool" and m["tool_call_id"] not in open_ids:
            continue
        result.append(m)
    return result


def build_context(session: ChatSession, max_messages: int = MAX_CONTEXT_MESSAGES) -> list[dict]:
    """组装发给模型的上下文：摘要（system）+ 最近 max_messages 条消息。系统提示词由调用方放在最前面。"""
    messages = []
    if session.summary:
        messages.append({"role": "system", "content": f"以下是之前对话的摘要：\n{session.summary}"})
    recent = list(unsummarized_messages(session).order_by("-seq_num")[:max_messages])[::-1]
    return messages + sanitize([to_unified(m) for m in recent])
