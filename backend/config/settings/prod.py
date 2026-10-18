from .base import *  # noqa: F401,F403

DEBUG = False

# 由 nginx 终止 HTTPS 时，信任其转发头
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
