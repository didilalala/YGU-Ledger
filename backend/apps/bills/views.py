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

    # TODO: 原项目创建/修改/删除账单时是否联动账户余额，需对照 bills.service.ts 核实后在此实现
    #       （如需联动，放在 transaction.atomic() 中并对账户 select_for_update()）

    @extend_schema(parameters=[StatisticsQuerySerializer], summary="收支统计")
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        query = StatisticsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(services.get_statistics(request.user, **query.validated_data))
