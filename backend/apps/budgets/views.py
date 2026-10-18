import calendar
from datetime import date

from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bills.models import Bill
from common.viewsets import UserOwnedViewSet

from .models import Budget
from .serializers import BudgetSerializer


def _period_range(period, today):
    if period == "monthly":
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=1), today.replace(day=last_day)
    return date(today.year, 1, 1), date(today.year, 12, 31)


class BudgetViewSet(UserOwnedViewSet):
    queryset = Budget.objects.select_related("category")
    serializer_class = BudgetSerializer
    pagination_class = None

    @action(detail=False, methods=["get"])
    def progress(self, request):
        """当前周期内各预算的使用情况。对应原项目 getBudgetProgress。"""
        today = date.today()
        results = []
        for budget in self.get_queryset().filter(is_active=True):
            start, end = _period_range(budget.period, today)
            bills = Bill.objects.filter(user=request.user, type="expense", date__range=(start, end))
            if budget.category_id:
                bills = bills.filter(category_id=budget.category_id)
            spent = bills.aggregate(s=Sum("amount"))["s"] or 0
            percentage = round(float(spent / budget.amount * 100), 1) if budget.amount else 0
            results.append({
                **BudgetSerializer(budget, context={"request": request}).data,
                "spent": float(spent),
                "remaining": float(budget.amount - spent),
                "percentage": percentage,
                "is_over_budget": spent > budget.amount,
                "is_alert": percentage >= budget.alert_at,
                "start_date": start,
                "end_date": end,
            })
        return Response(results)
