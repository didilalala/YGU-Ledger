import pytest
from cryptography.fernet import Fernet
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture(autouse=True)
def _settings(settings):
    settings.FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()


@pytest.fixture
def user(db):
    return User.objects.create_user("alice", "secret123")


@pytest.fixture
def client(user):
    c = APIClient()
    resp = c.post("/api/auth/login", {"username": "alice", "password": "secret123"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['token']}")
    return c


@pytest.fixture
def other_client(db):
    User.objects.create_user("bob", "secret123")
    c = APIClient()
    resp = c.post("/api/auth/login", {"username": "bob", "password": "secret123"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['token']}")
    return c
