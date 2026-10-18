from django.conf import settings
from django.db import models

from apps.categories.models import TYPE_CHOICES


class Bill(models.Model):
    """对应 Prisma 模型 Bill。"""

    SOURCE_CHOICES = [
        ("manual", "手动"), ("voice", "语音"), ("ocr", "拍照"),
        ("text", "AI 文本"), ("notification", "支付通知"),
    ]

    amount = models.DecimalField("金额", max_digits=15, decimal_places=4)
    type = models.CharField("类型", max_length=10, choices=TYPE_CHOICES)
    description = models.TextField("描述", null=True, blank=True)
    date = models.DateField("日期")
    time = models.DateTimeField("具体时间", null=True, blank=True)
    category = models.ForeignKey("categories.Category", on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="bills")
    account = models.ForeignKey("accounts.Account", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="bills")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bills")
    # MySQL 没有数组类型，原 String[] 改为 JSON 列表
    tags = models.JSONField("标签", default=list, blank=True)
    notes = models.TextField("备注", null=True, blank=True)
    receipt_url = models.TextField("收据图片", null=True, blank=True)
    source = models.CharField("来源", max_length=20, choices=SOURCE_CHOICES, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bills"
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "type"]),
            models.Index(fields=["source"]),
        ]
        verbose_name = verbose_name_plural = "账单"

    def __str__(self):
        return f"{self.date} {self.get_type_display()} {self.amount}"
