"""
账单统计。对应原项目 bills.service.ts getStatistics。
"""
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth

from .models import Bill


def filter_by_date(qs, start_date=None, end_date=None):
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    return qs


def _category_breakdown(qs, total):
    rows = (qs.values("category_id", "category__name", "category__icon")
              .annotate(amount=Sum("amount"), count=Count("id"))
              .order_by("-amount"))
    return [{
        "category_id": r["category_id"],
        "category_name": r["category__name"] or "未分类",
        "category_icon": r["category__icon"] or "📊",
        "amount": float(r["amount"]),
        "percentage": round(float(r["amount"] / total * 100), 1) if total else 0,
        "count": r["count"],
    } for r in rows]


def get_statistics(user, start_date=None, end_date=None, granularity="daily", category_id=None):
    qs = filter_by_date(Bill.objects.filter(user=user), start_date, end_date)
    if category_id:
        qs = qs.filter(category_id=category_id)
    income_qs, expense_qs = qs.filter(type="income"), qs.filter(type="expense")

    income = income_qs.aggregate(s=Sum("amount"), c=Count("id"))
    expense = expense_qs.aggregate(s=Sum("amount"), c=Count("id"))
    total_income, total_expense = income["s"] or Decimal(0), expense["s"] or Decimal(0)

    # 趋势：按日或按月汇总。日期截断在 Django 层做，避免依赖 MySQL 时区表
    trunc = TruncMonth("date") if granularity == "monthly" else TruncDay("date")
    trend_rows = (qs.annotate(period=trunc).values("period", "type")
                    .annotate(amount=Sum("amount")).order_by("period"))
    trend = {}
    for r in trend_rows:
        key = r["period"].strftime("%Y-%m" if granularity == "monthly" else "%Y-%m-%d")
        item = trend.setdefault(key, {"period": key, "income": 0.0, "expense": 0.0})
        item[r["type"]] = float(r["amount"])

    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "balance": float(total_income - total_expense),
        "income_count": income["c"],
        "expense_count": expense["c"],
        "expense_by_category": _category_breakdown(expense_qs, total_expense),
        "income_by_category": _category_breakdown(income_qs, total_income),
        "trend": list(trend.values()),
    }
