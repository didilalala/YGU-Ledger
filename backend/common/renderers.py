"""
统一响应渲染器：所有成功响应包装为 {code, message, data, success}，字段转驼峰。
对应原项目 common/interceptors/response.interceptor.ts。
"""
from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class ApiRenderer(CamelCaseJSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        already_wrapped = isinstance(data, dict) and "code" in data and "message" in data
        if response is not None and not already_wrapped:
            data = {
                "code": response.status_code,
                "message": "操作成功",
                "data": data,
                "success": response.status_code < 400,
            }
        return super().render(data, accepted_media_type, renderer_context)
