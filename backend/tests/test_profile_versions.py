"""个人资料、头像上传、修改密码与应用版本检查。"""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.users.models import User
from apps.versions.models import AppVersion


def png_bytes(size=(8, 8)):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------- 资料

def test_update_nickname_and_email(client):
    resp = client.patch("/api/auth/profile", {"nickname": "小艾", "email": "a@example.com"}, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["nickname"] == "小艾" and data["email"] == "a@example.com" and data["username"] == "alice"


def test_clear_email_with_null(client):
    client.patch("/api/auth/profile", {"email": "a@example.com"}, format="json")
    resp = client.patch("/api/auth/profile", {"email": None}, format="json")
    assert resp.status_code == 200 and resp.json()["data"]["email"] is None


def test_email_must_be_unique_and_valid(client, other_client):
    other_client.patch("/api/auth/profile", {"email": "taken@example.com"}, format="json")
    assert client.patch("/api/auth/profile", {"email": "taken@example.com"}, format="json").status_code == 400
    assert client.patch("/api/auth/profile", {"email": "not-an-email"}, format="json").status_code == 400


def test_username_and_avatar_cannot_be_changed_via_profile(client):
    resp = client.patch("/api/auth/profile", {"username": "hacker", "avatar": "http://evil/x.png"}, format="json")
    data = resp.json()["data"]
    assert data["username"] == "alice" and data["avatar"] is None


# ---------------------------------------------------------------- 密码

def test_change_password_flow(client):
    assert client.patch("/api/auth/password", {"oldPassword": "wrong", "newPassword": "newpass123"},
                        format="json").status_code == 400
    assert client.patch("/api/auth/password", {"oldPassword": "secret123", "newPassword": "123"},
                        format="json").status_code == 400  # 太短
    assert client.patch("/api/auth/password", {"oldPassword": "secret123", "newPassword": "newpass123"},
                        format="json").status_code == 200

    from rest_framework.test import APIClient
    fresh = APIClient()
    assert fresh.post("/api/auth/login", {"username": "alice", "password": "secret123"}, format="json").status_code == 401
    assert fresh.post("/api/auth/login", {"username": "alice", "password": "newpass123"}, format="json").status_code == 200


# ---------------------------------------------------------------- 头像

def test_upload_avatar(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload = SimpleUploadedFile("me.png", png_bytes(), content_type="image/png")
    resp = client.post("/api/auth/avatar", {"file": upload}, format="multipart")
    assert resp.status_code == 200
    url = resp.json()["data"]["avatar"]
    assert "/media/avatars/" in url and url.endswith(".png")
    assert len(list((tmp_path / "avatars").iterdir())) == 1
    assert User.objects.get(username="alice").avatar == url


def test_upload_avatar_rejects_non_image(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    fake = SimpleUploadedFile("evil.png", b"<?php echo 1; ?>", content_type="image/png")
    resp = client.post("/api/auth/avatar", {"file": fake}, format="multipart")
    assert resp.status_code == 400 and resp.json()["success"] is False
    assert not (tmp_path / "avatars").exists()


def test_avatar_extension_comes_from_content_not_filename(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "blue").save(buf, format="JPEG")
    upload = SimpleUploadedFile("photo.png", buf.getvalue(), content_type="image/png")  # 名字是 png，内容是 jpeg
    resp = client.post("/api/auth/avatar", {"file": upload}, format="multipart")
    assert resp.status_code == 200 and resp.json()["data"]["avatar"].endswith(".jpg")
    assert [p.suffix for p in (tmp_path / "avatars").iterdir()] == [".jpg"]


def test_avatar_rejects_non_image_extension_even_with_image_content(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload = SimpleUploadedFile("shell.php", png_bytes(), content_type="image/png")
    resp = client.post("/api/auth/avatar", {"file": upload}, format="multipart")
    assert resp.status_code == 400
    assert not (tmp_path / "avatars").exists()


def test_avatar_rejects_unsupported_image_format(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="BMP")
    upload = SimpleUploadedFile("a.bmp", buf.getvalue(), content_type="image/bmp")
    resp = client.post("/api/auth/avatar", {"file": upload}, format="multipart")
    assert resp.status_code == 400 and "仅支持" in resp.json()["message"]


def test_upload_avatar_requires_file(client):
    assert client.post("/api/auth/avatar", {}, format="multipart").status_code == 400


# ---------------------------------------------------------------- 版本

@pytest.fixture
def versions(db):
    def make(code, force=False, platform="android"):
        return AppVersion.objects.create(version=f"1.0.{code}-{platform}", version_code=code, platform=platform,
                                         download_url=f"https://example.com/{code}.apk", update_log=f"更新{code}",
                                         force_update=force)
    return make


def check(code, platform="android"):
    from rest_framework.test import APIClient
    return APIClient().get("/api/app-version/check", {"versionCode": code, "platform": platform}).json()["data"]


def test_check_update_available_and_up_to_date(versions):
    versions(100)
    versions(102)
    data = check(100)
    assert data["hasUpdate"] is True and data["forceUpdate"] is False
    assert data["latest"]["versionCode"] == 102 and data["latest"]["downloadUrl"].endswith("102.apk")
    assert check(102) == {"hasUpdate": False, "forceUpdate": False, "latest": None}
    assert check(200)["hasUpdate"] is False


def test_force_update_if_any_skipped_version_is_forced(versions):
    versions(101, force=True)
    versions(102)  # 最新版不强制，但中间跳过了一个强制版本
    assert check(100)["forceUpdate"] is True
    assert check(101)["forceUpdate"] is False  # 已经装了强制版本，只剩普通更新


def test_check_update_by_platform_and_no_versions(versions):
    assert check(1)["hasUpdate"] is False  # 还没有任何发布
    versions(500, platform="ios")
    assert check(1, "android")["hasUpdate"] is False
    assert check(1, "ios")["hasUpdate"] is True


def test_latest_endpoint(versions):
    from rest_framework.test import APIClient
    assert APIClient().get("/api/app-version/latest").json()["data"] is None
    versions(100)
    versions(105)
    assert APIClient().get("/api/app-version/latest").json()["data"]["versionCode"] == 105
