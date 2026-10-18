"""
会话与消息持久化。对应原项目 ai/services/session.service.ts。
"""
from django.db import transaction
from django.db.models import Max

from ..models import ChatMessage, ChatSession


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


def build_context(session: ChatSession, max_messages: int = 30) -> list[dict]:
    """
    组装发给模型的上下文：摘要 + 最近若干条消息，转换为 adapters/base.py 中的统一消息格式。
    TODO: 参照原项目的摘要压缩策略（summary / summary_up_to），在消息过多时生成摘要
    """
    messages = []
    if session.summary:
        messages.append({"role": "system", "content": f"之前对话的摘要：{session.summary}"})
    qs = session.messages.all()
    if session.summary_up_to:
        qs = qs.filter(seq_num__gt=session.summary_up_to)
    for m in list(qs.order_by("-seq_num")[:max_messages])[::-1]:
        item = {"role": m.role, "content": m.content}
        if m.tool_calls:
            item["tool_calls"] = m.tool_calls
        if m.role == "tool":
            item.update(tool_call_id=m.tool_call_id, tool_name=m.tool_name)
        messages.append(item)
    return messages
