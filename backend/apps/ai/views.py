import json
import logging

from asgiref.sync import async_to_sync, sync_to_async
from django.core.exceptions import RequestDataTooBig
from django.db import transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from djangorestframework_camel_case.util import camelize, underscoreize
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.exceptions import BusinessError
from common.viewsets import UserOwnedViewSet

from .adapters import get_adapter
from .models import AIModelConfig, ChatSession
from .serializers import (
    AIModelConfigSerializer,
    AsrRequestSerializer,
    ChatRequestSerializer,
    ChatSessionDetailSerializer,
    ChatSessionSerializer,
)
from .services import asr, chat

logger = logging.getLogger(__name__)


class AIModelConfigViewSet(UserOwnedViewSet):
    """AI 模型配置。对应原项目 ai-config.controller.ts。"""

    queryset = AIModelConfig.objects.all()
    serializer_class = AIModelConfigSerializer
    pagination_class = None

    def perform_create(self, serializer):
        # 第一个配置自动成为默认，否则用户填完 Key 去聊天还会提示"请先配置 AI 模型"
        first = not self.get_queryset().exists()
        serializer.save(user=self.request.user, is_default=first)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        config = self.get_object()
        with transaction.atomic():
            self.get_queryset().update(is_default=False)
            config.is_default = True
            config.save(update_fields=["is_default"])
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        adapter = get_adapter(self.get_object())
        try:
            async_to_sync(adapter.test_connection)()
        except Exception as exc:
            logger.warning("AI 连接测试失败: %s", exc)
            return Response({"success": False, "message": str(exc)})
        return Response({"success": True, "message": "连接成功"})


class ChatSessionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """会话列表 / 详情 / 改标题 / 置顶 / 删除。对应原项目 chat.controller.ts 的 sessions 部分。"""

    queryset = ChatSession.objects.none()  # 仅供接口文档推断类型，实际查询见 get_queryset
    serializer_class = ChatSessionSerializer
    http_method_names = ["get", "patch", "post", "delete"]

    def get_queryset(self):
        qs = ChatSession.objects.filter(user=self.request.user, is_active=True)
        if self.action == "retrieve":
            qs = qs.prefetch_related("messages")
        return qs

    def get_serializer_class(self):
        return ChatSessionDetailSerializer if self.action == "retrieve" else ChatSessionSerializer

    def perform_destroy(self, instance):
        instance.is_active = False  # 软删除，与原项目一致
        instance.save(update_fields=["is_active"])

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response({"code": 200, "message": "删除成功", "data": None, "success": True})

    @action(detail=True, methods=["post"], url_path="toggle-pin")
    def toggle_pin(self, request, pk=None):
        session = self.get_object()
        session.is_pinned = not session.is_pinned
        session.save(update_fields=["is_pinned"])
        return Response(ChatSessionSerializer(session).data)


class ChatSendView(APIView):
    serializer_class = ChatRequestSerializer

    @extend_schema(request=ChatRequestSerializer, summary="发送消息（非流式）")
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(chat.send(request.user, serializer.validated_data))
        except NotImplementedError:
            raise BusinessError("对话功能尚未实现", status=501)


def _authenticate(request):
    """流式接口不走 DRF，手动校验 JWT。"""
    result = JWTAuthentication().authenticate(request)
    if result is None:
        raise AuthenticationFailed("未授权访问")
    return result[0]


@csrf_exempt
async def chat_stream(request):
    """
    流式对话（SSE）。不使用 DRF APIView，因为 DRF 不支持异步视图。
    前端：POST JSON（驼峰字段），响应为 text/event-stream。
    """
    if request.method != "POST":
        return JsonResponse({"code": 405, "message": "请求方法不被允许", "data": None, "success": False}, status=405)
    try:
        user = await sync_to_async(_authenticate)(request)
    except AuthenticationFailed:
        return JsonResponse({"code": 401, "message": "未授权访问", "data": None, "success": False}, status=401)

    try:
        body = json.loads(request.body or b"{}")
    except RequestDataTooBig:
        return JsonResponse({"code": 413, "message": "请求内容过大，请减少图片数量或压缩图片", "data": None,
                             "success": False}, status=413)
    except ValueError:
        return JsonResponse({"code": 400, "message": "请求体不是合法的 JSON", "data": None, "success": False},
                            status=400)

    serializer = ChatRequestSerializer(data=underscoreize(body))
    if not serializer.is_valid():
        return JsonResponse({"code": 400, "message": "请求参数错误", "data": serializer.errors,
                             "success": False}, status=400)

    async def event_stream():
        async for event in chat.stream(user, serializer.validated_data):
            # 与其他接口一致，事件字段转驼峰（session_id → sessionId）
            yield f"data: {json.dumps(camelize(event), ensure_ascii=False, default=str)}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # 告诉 nginx 不要缓冲
    return response


class AsrTranscribeView(APIView):
    serializer_class = AsrRequestSerializer

    @extend_schema(request=AsrRequestSerializer, summary="语音转文字")
    def post(self, request):
        serializer = AsrRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = asr.transcribe(serializer.validated_data["audio"], serializer.validated_data["mime_type"])
        return Response({"text": text})


class ParseBillsView(APIView):
    """旧接口：从文本/图片中直接解析账单（不走对话）。对应原项目 ai.controller.ts parse-bills。"""

    serializer_class = ChatRequestSerializer  # TODO: 替换为专用的解析请求序列化器

    def post(self, request):
        # TODO: 使用默认 AI 配置 + 原项目 BILL_PARSE_PROMPT 解析，返回账单数组
        raise BusinessError("账单解析尚未实现", status=501)
