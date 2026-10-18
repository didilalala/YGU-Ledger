from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response

from common.viewsets import UserOwnedViewSet

from .models import Account
from .serializers import AccountSerializer


class AccountViewSet(UserOwnedViewSet):
    """账户。余额是用户手动维护的字段，不随账单自动变化（与原项目一致）。"""

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = None

    def get_queryset(self):
        # 默认账户在前，其次按排序号，最后新建的在前
        return super().get_queryset().order_by("-is_default", "sort_order", "-created_at")

    def _clear_other_defaults(self, serializer, exclude_id=None):
        """设为默认账户时，取消该用户其他账户的默认标记。"""
        if serializer.validated_data.get("is_default"):
            others = Account.objects.filter(user=self.request.user, is_default=True)
            if exclude_id:
                others = others.exclude(id=exclude_id)
            others.update(is_default=False)

    @transaction.atomic
    def perform_create(self, serializer):
        self._clear_other_defaults(serializer)
        serializer.save(user=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        self._clear_other_defaults(serializer, exclude_id=serializer.instance.id)
        serializer.save()

    @action(detail=False, methods=["get"])
    def balance(self, request):
        """资产 / 负债 / 净资产汇总。信用卡的余额计入负债，其余账户计入资产。对应原项目 getTotalBalance。"""
        assets = liabilities = 0.0
        for account in self.get_queryset():
            if account.type == "credit_card":
                liabilities += abs(float(account.balance))
            else:
                assets += float(account.balance)
        return Response({"total_assets": assets, "total_liabilities": liabilities,
                         "net_worth": assets - liabilities})
