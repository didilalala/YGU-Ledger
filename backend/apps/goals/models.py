from django.conf import settings
from django.db import models


class FinancialGoal(models.Model):
    """对应 Prisma 模型 FinancialGoal。"""

    name = models.CharField("目标名称", max_length=100)
    target_amount = models.DecimalField("目标金额", max_digits=15, decimal_places=4)
    current_amount = models.DecimalField("当前金额", max_digits=15, decimal_places=4, default=0)
    deadline = models.DateField("截止日期", null=True, blank=True)
    icon = models.CharField("图标(emoji)", max_length=10, null=True, blank=True)
    color = models.CharField("颜色", max_length=20, null=True, blank=True)
    is_completed = models.BooleanField("已完成", default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="financial_goals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_goals"
        verbose_name = verbose_name_plural = "财务目标"

    def __str__(self):
        return self.name
