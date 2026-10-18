from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppVersion


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ["version", "version_code", "download_url", "update_log", "force_update", "platform", "created_at"]


class CheckView(APIView):
    """检查更新：?versionCode=10203&platform=android"""

    serializer_class = AppVersionSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        current = int(request.query_params.get("version_code", 0))
        platform = request.query_params.get("platform", "android")
        latest = AppVersion.objects.filter(platform=platform).first()
        has_update = bool(latest and latest.version_code > current)
        # 跨越的版本中只要有一个强制更新，就要求强制更新
        force = has_update and AppVersion.objects.filter(
            platform=platform, version_code__gt=current, force_update=True).exists()
        return Response({
            "has_update": has_update,
            "force_update": force,
            "latest": AppVersionSerializer(latest).data if has_update else None,
        })


class LatestView(APIView):
    serializer_class = AppVersionSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        latest = AppVersion.objects.filter(platform=request.query_params.get("platform", "android")).first()
        return Response(AppVersionSerializer(latest).data if latest else None)
