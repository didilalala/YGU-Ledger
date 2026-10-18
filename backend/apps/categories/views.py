from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response

from common.exceptions import BusinessError
from common.viewsets import UserOwnedViewSet

from .models import DEFAULT_CATEGORIES, Category
from .serializers import CategorySerializer


class CategoryViewSet(UserOwnedViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        # 列表与详情：系统默认分类 + 自己的分类；修改/删除只能操作自己的
        qs = Category.objects.all()
        if self.action in ("list", "retrieve"):
            qs = qs.filter(Q(user=self.request.user) | Q(user__isnull=True))
        else:
            qs = qs.filter(user=self.request.user)
        if type_ := self.request.query_params.get("type"):
            qs = qs.filter(type=type_)
        return qs

    @action(detail=False, methods=["post"], url_path="init-defaults")
    def init_defaults(self, request):
        """初始化系统默认分类（仅管理员）。"""
        if not request.user.is_staff:
            raise BusinessError("仅管理员可初始化默认分类", status=403)
        created = 0
        for order, (name, type_, icon) in enumerate(DEFAULT_CATEGORIES):
            _, is_new = Category.objects.get_or_create(
                user=None, name=name, type=type_,
                defaults={"icon": icon, "is_default": True, "sort_order": order},
            )
            created += is_new
        return Response({"created": created})
