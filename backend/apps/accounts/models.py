from django.conf import settings
from django.db import models


class Account(models.Model):
    """对应 Prisma 模型 Account。"""

    TYPE_CHOICES = [
        ("bank_card", "银行卡"), ("e_wallet", "电子钱包"),
        ("credit_card", "信用卡"), ("cash", "现金"),
    ]

    name = models.CharField("账户名称", max_length=100)
    type = models.CharField("账户类型", max_length=20, choices=TYPE_CHOICES)
    balance = models.DecimalField("余额", max_digits=15, decimal_places=4, default=0)
    icon = models.CharField("图标(emoji)", max_length=10, null=True, blank=True)
    color = models.CharField("颜色", max_length=20, null=True, blank=True)
    is_default = models.BooleanField("默认账户", default=False)
    sort_order = models.IntegerField("排序", default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts"
        ordering = ["sort_order", "id"]
        indexes = [models.Index(fields=["user", "type"])]
        verbose_name = verbose_name_plural = "账户"

    def __str__(self):
        return self.name
