from django.conf import settings
from django.db import models


class Budget(models.Model):
    """对应 Prisma 模型 Budget。category 为空表示总预算。"""

    PERIOD_CHOICES = [("monthly", "每月"), ("yearly", "每年")]

    name = models.CharField("预算名称", max_length=100)
    amount = models.DecimalField("预算金额", max_digits=15, decimal_places=4)
    period = models.CharField("周期", max_length=20, choices=PERIOD_CHOICES)
    category = models.ForeignKey("categories.Category", on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="budgets")
    alert_at = models.IntegerField("提醒百分比", default=80)
    is_active = models.BooleanField("启用", default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budgets"
        indexes = [models.Index(fields=["user", "period"])]
        verbose_name = verbose_name_plural = "预算"

    def __str__(self):
        return self.name
