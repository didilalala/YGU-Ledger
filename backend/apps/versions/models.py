from django.db import models


class AppVersion(models.Model):
    """对应 Prisma 模型 AppVersion。版本由管理员在 Django Admin 中发布。"""

    version = models.CharField("版本号", max_length=20, unique=True)
    version_code = models.IntegerField("版本码", unique=True)
    download_url = models.TextField("下载链接")
    update_log = models.TextField("更新日志")
    force_update = models.BooleanField("强制更新", default=False)
    platform = models.CharField("平台", max_length=20, default="android")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "app_versions"
        ordering = ["-version_code"]
        indexes = [models.Index(fields=["platform"])]
        verbose_name = verbose_name_plural = "应用版本"

    def __str__(self):
        return f"{self.platform} {self.version}"
