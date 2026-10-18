from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from common.viewsets import UserOwnedViewSet

from .models import Account
from .serializers import AccountSerializer


class AccountViewSet(UserOwnedViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = None

    @action(detail=False, methods=["get"])
    def balance(self, request):
        """所有账户的总余额。"""
        total = self.get_queryset().aggregate(total=Sum("balance"))["total"] or 0
        return Response({"totalBalance": float(total), "accountCount": self.get_queryset().count()})
