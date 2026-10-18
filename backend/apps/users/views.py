import uuid

from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.exceptions import BusinessError

from .serializers import (
    AvatarSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


AVATAR_EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "GIF": "gif", "WEBP": "webp"}


def _token_for(user):
    return str(RefreshToken.for_user(user).access_token)


class RegisterView(APIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, summary="用户注册")
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data, "token": _token_for(user)},
                        status=status.HTTP_201_CREATED)


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer, summary="用户登录")
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request,
                            username=serializer.validated_data["username"].lower(),
                            password=serializer.validated_data["password"])
        if user is None:
            raise BusinessError("用户名或密码错误", status=401)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return Response({"user": UserSerializer(user).data, "token": _token_for(user)})


class ProfileView(APIView):
    @extend_schema(responses=UserSerializer, summary="获取当前用户信息")
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=UserSerializer, responses=UserSerializer, summary="修改个人资料")
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    serializer_class = ChangePasswordSerializer

    @extend_schema(request=ChangePasswordSerializer, summary="修改密码")
    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"code": 200, "message": "密码修改成功", "data": None, "success": True})


class AvatarView(APIView):
    serializer_class = AvatarSerializer

    @extend_schema(request={"multipart/form-data": AvatarSerializer}, summary="上传头像")
    def post(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        # 扩展名由检测到的图片格式决定，不信任用户给的文件名（避免把 x.php 这类名字原样落盘）
        ext = AVATAR_EXTENSIONS.get(file.image.format)
        if ext is None:
            raise BusinessError("仅支持 JPG、PNG、GIF、WebP 格式的图片")
        path = default_storage.save(f"avatars/{uuid.uuid4().hex}.{ext}", file)
        request.user.avatar = request.build_absolute_uri(default_storage.url(path))
        request.user.save(update_fields=["avatar"])
        return Response(UserSerializer(request.user).data)
