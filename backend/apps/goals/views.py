from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from common.viewsets import UserOwnedViewSet

from .models import FinancialGoal
from .serializers import FinancialGoalSerializer


class FinancialGoalViewSet(UserOwnedViewSet):
    queryset = FinancialGoal.objects.all()
    serializer_class = FinancialGoalSerializer
    pagination_class = None

    @action(detail=False, methods=["get"])
    def progress(self, request):
        """所有目标的汇总进度。"""
        qs = self.get_queryset()
        agg = qs.aggregate(target=Sum("target_amount"), current=Sum("current_amount"))
        target, current = agg["target"] or 0, agg["current"] or 0
        return Response({
            "total_goals": qs.count(),
            "completed_goals": qs.filter(is_completed=True).count(),
            "total_target": float(target),
            "total_current": float(current),
            "overall_progress": round(float(current / target * 100), 1) if target else 0,
        })
