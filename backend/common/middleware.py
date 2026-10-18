import logging
import time

logger = logging.getLogger("request")


class RequestLogMiddleware:
    """记录每个请求的方法、路径、状态码与耗时。对应原项目 logger.middleware.ts。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        cost = (time.monotonic() - start) * 1000
        logger.info("%s %s %s %.0fms", request.method, request.get_full_path(), response.status_code, cost)
        return response
