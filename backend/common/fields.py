"""
加密字段：用于 AI API Key 等敏感数据，数据库中存 Fernet 密文。
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


def _fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise ImproperlyConfigured("未配置 FIELD_ENCRYPTION_KEY，无法加解密敏感字段")
    return Fernet(key.encode())


class EncryptedTextField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # 兼容迁移前的明文数据
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return _fernet().encrypt(value.encode()).decode()


def mask_secret(value, visible=4):
    """接口返回时只显示末尾几位。"""
    if not value:
        return ""
    return "*" * max(len(value) - visible, 0) + value[-visible:]
