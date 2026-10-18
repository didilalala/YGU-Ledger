"""
统一异常处理。对应原项目 common/filters/http-exception.filter.ts。
"""
import logging

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    400: "请求参数错误",
    401: "未授权访问",
    403: "禁止访问",
    404: "请求的资源不存在",
    405: "请求方法不被允许",
    409: "请求冲突",
    422: "请求参数验证失败",
    429: "请求过于频繁",
    500: "服务器内部错误",
}


class BusinessError(Exception):
    """业务异常：在 service 层抛出，自动转换为对应状态码的响应。"""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _first_error(detail):
    """从 DRF 嵌套的错误结构中取出第一条可读信息。"""
    if isinstance(detail, list) and detail:
        return _first_error(detail[0])
    if isinstance(detail, dict) and detail:
        return _first_error(next(iter(detail.values())))
    return str(detail)


def api_exception_handler(exc, context):
    request = context.get("request")
    path = request.get_full_path() if request else ""

    if isinstance(exc, BusinessError):
        status, message, details = exc.status, exc.message, None
    else:
        response = exception_handler(exc, context)
        if response is None:
            logger.exception("未处理异常: %s", path)
            status, message, details = 500, STATUS_MESSAGES[500], str(exc)
        else:
            status = response.status_code
            details = response.data
            if isinstance(exc, ValidationError):
                message = _first_error(response.data)
            else:
                message = getattr(exc, "detail", None) and str(exc.detail) or STATUS_MESSAGES.get(status, "请求失败")

    body = {
        "code": status,
        "message": message,
        "data": None,
        "success": False,
        "timestamp": timezone.now().isoformat(),
        "path": path,
    }
    if settings.DEBUG and details is not None:
        body["details"] = details
    return Response(body, status=status)
