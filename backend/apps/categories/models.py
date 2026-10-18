from django.conf import settings
from django.db import models

TYPE_CHOICES = [("income", "收入"), ("expense", "支出")]


class Category(models.Model):
    """对应 Prisma 模型 Category。user 为空表示系统默认分类。"""

    name = models.CharField("分类名称", max_length=100)
    type = models.CharField("类型", max_length=10, choices=TYPE_CHOICES)
    icon = models.CharField("图标(emoji)", max_length=10, null=True, blank=True)
    color = models.CharField("颜色", max_length=20, null=True, blank=True)
    is_default = models.BooleanField("系统默认", default=False)
    sort_order = models.IntegerField("排序", default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["is_default"]),
        ]
        verbose_name = verbose_name_plural = "分类"

    def __str__(self):
        return f"{self.icon or ''}{self.name}"


# 与原项目 categories.service.ts initDefaultCategories 保持一致
DEFAULT_CATEGORIES = [
    ("餐饮", "expense", "🍔"), ("交通", "expense", "🚗"), ("购物", "expense", "🛍️"),
    ("娱乐", "expense", "🎮"), ("医疗", "expense", "🏥"), ("教育", "expense", "📚"),
    ("住房", "expense", "🏠"), ("其他", "expense", "📝"),
    ("工资", "income", "💰"), ("奖金", "income", "🎁"), ("投资", "income", "📈"),
    ("兼职", "income", "💼"), ("其他", "income", "📝"),
]
