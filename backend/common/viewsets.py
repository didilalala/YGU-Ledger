from rest_framework import status, viewsets
from rest_framework.response import Response


class UserOwnedViewSet(viewsets.ModelViewSet):
    """
    属于当前用户的资源的通用 CRUD：
    - 查询自动按 request.user 过滤，避免越权
    - 创建时自动写入 user
    - 删除返回 200 + 统一响应体（原项目前端按 JSON 解析删除结果）
    """

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response({"code": 200, "message": "删除成功", "data": None, "success": True},
                        status=status.HTTP_200_OK)
