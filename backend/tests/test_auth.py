from rest_framework.test import APIClient


def test_register_returns_envelope_and_token(db):
    resp = APIClient().post("/api/auth/register",
                            {"username": "NewUser", "password": "secret123", "nickname": "新用户"}, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True and body["code"] == 201
    assert body["data"]["user"]["username"] == "newuser"  # 统一小写
    assert body["data"]["user"]["createdAt"]  # 驼峰输出
    assert body["data"]["token"]


def test_register_duplicate_username(user):
    resp = APIClient().post("/api/auth/register", {"username": "ALICE", "password": "secret123"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["message"] == "用户名已存在"
    assert resp.json()["success"] is False


def test_login_wrong_password(user):
    resp = APIClient().post("/api/auth/login", {"username": "alice", "password": "bad"}, format="json")
    assert resp.status_code == 401
    assert resp.json()["message"] == "用户名或密码错误"


def test_profile_requires_auth(db):
    resp = APIClient().get("/api/auth/profile")
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_profile_and_change_password(client):
    assert client.get("/api/auth/profile").json()["data"]["username"] == "alice"
    resp = client.patch("/api/auth/password", {"oldPassword": "secret123", "newPassword": "newpass456"}, format="json")
    assert resp.status_code == 200
    login = APIClient().post("/api/auth/login", {"username": "alice", "password": "newpass456"}, format="json")
    assert login.status_code == 200


def test_legacy_bcrypt_hash_still_logs_in(user):
    """从原 NestJS 项目迁移来的 bcrypt 哈希（补上 bcrypt$ 前缀后）可以直接登录。"""
    import bcrypt

    user.password = "bcrypt$" + bcrypt.hashpw(b"legacy123", bcrypt.gensalt()).decode()
    user.save()
    resp = APIClient().post("/api/auth/login", {"username": "alice", "password": "legacy123"}, format="json")
    assert resp.status_code == 200
