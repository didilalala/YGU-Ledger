import asyncio

from django.db import connection

from apps.ai.models import AIModelConfig


def test_api_key_encrypted_and_masked(client):
    resp = client.post("/api/ai/configs", {"name": "我的 DeepSeek", "provider": "deepseek",
                                           "apiKey": "sk-1234567890abcd", "model": "deepseek-chat"}, format="json")
    data = resp.json()["data"]
    assert "apiKey" not in data
    assert data["apiKeyMasked"].endswith("abcd") and "1234" not in data["apiKeyMasked"]

    with connection.cursor() as cur:
        cur.execute("SELECT api_key FROM ai_model_configs WHERE id = %s", [data["id"]])
        assert "sk-123" not in cur.fetchone()[0]  # 数据库中是密文
    assert AIModelConfig.objects.get(id=data["id"]).api_key == "sk-1234567890abcd"


def test_set_default_is_exclusive(client):
    ids = [client.post("/api/ai/configs", {"name": n, "provider": "openai", "apiKey": "k",
                                           "model": "gpt"}, format="json").json()["data"]["id"] for n in "ab"]
    client.post(f"/api/ai/configs/{ids[0]}/set-default")
    client.post(f"/api/ai/configs/{ids[1]}/set-default")
    defaults = list(AIModelConfig.objects.filter(is_default=True).values_list("id", flat=True))
    assert defaults == [ids[1]]


def test_chat_stream_requires_auth(db):
    from django.test import Client

    resp = Client().post("/api/ai/chat/stream", {}, content_type="application/json")
    assert resp.status_code == 401


def test_chat_sessions_soft_delete(client, user):
    from apps.ai.models import ChatSession

    session = ChatSession.objects.create(user=user, title="测试")
    assert len(client.get("/api/ai/chat/sessions").json()["data"]["items"]) == 1
    client.post(f"/api/ai/chat/sessions/{session.id}/toggle-pin")
    client.delete(f"/api/ai/chat/sessions/{session.id}")
    assert client.get("/api/ai/chat/sessions").json()["data"]["items"] == []
    session.refresh_from_db()
    assert session.is_active is False and session.is_pinned is True


def test_chat_stream_events_are_camelcased(client, monkeypatch):
    from django.test import Client

    from apps.ai.services import chat

    async def fake_stream(user, payload):
        yield {"event": "session_created", "data": {"session_id": 7}}
        yield {"event": "text_delta", "data": {"content": f"收到：{payload['message']}"}}

    monkeypatch.setattr(chat, "stream", fake_stream)
    token = client._credentials["HTTP_AUTHORIZATION"]
    resp = Client().post("/api/ai/chat/stream", {"message": "你好", "sessionId": None},
                         content_type="application/json", HTTP_AUTHORIZATION=token)
    assert resp["Content-Type"] == "text/event-stream"
    # 异步视图返回的是异步迭代器
    async def read_all():
        return b"".join([chunk async for chunk in resp.streaming_content])

    body = asyncio.run(read_all()).decode()
    assert 'data: {"event": "session_created", "data": {"sessionId": 7}}\n\n' in body
    assert "收到：你好" in body
