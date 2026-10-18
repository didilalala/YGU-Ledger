from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from common.viewsets import UserOwnedViewSet

from . import services
from .models import Bill
from .serializers import BillQuerySerializer, BillSerializer, StatisticsQuerySerializer


class BillViewSet(UserOwnedViewSet):
    queryset = Bill.objects.select_related("category")
    serializer_class = BillSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs
        query = BillQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        p = query.validated_data
        if "type" in p:
            qs = qs.filter(type=p["type"])
        if "category_id" in p:
            qs = qs.filter(category_id=p["category_id"])
        qs = services.filter_by_date(qs, p.get("start_date"), p.get("end_date"))
        prefix = "-" if p["order_direction"] == "desc" else ""
        return qs.order_by(f"{prefix}{p['order_by']}", f"{prefix}id")

    # 不联动账户余额：已对照原项目 bills.service.ts，其创建 / 修改 / 删除账单时都不改账户余额，
    # 账户余额是用户在账户页手动维护的字段（accounts.service.ts 也只做汇总）。这里保持一致。

    @extend_schema(parameters=[StatisticsQuerySerializer], summary="收支统计")
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        query = StatisticsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(services.get_statistics(request.user, **query.validated_data))
