from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# 开发时 runserver 自己提供静态文件，不需要 WhiteNoise（否则会因缺少 staticfiles 目录告警）
MIDDLEWARE = [m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"]  # noqa: F405

# 开发时额外启用可浏览 API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "common.renderers.ApiRenderer",
    "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
]
