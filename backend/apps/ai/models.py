from django.conf import settings
from django.db import models

from common.fields import EncryptedTextField


class AIModelConfig(models.Model):
    """对应 Prisma 模型 AIModelConfig。API Key 加密存储。"""

    PROVIDER_CHOICES = [("claude", "Claude"), ("openai", "OpenAI"), ("deepseek", "DeepSeek"), ("qwen", "Qwen")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_configs")
    name = models.CharField("显示名称", max_length=100)
    provider = models.CharField("服务商", max_length=50, choices=PROVIDER_CHOICES)
    api_key = EncryptedTextField("API Key")
    api_base_url = models.CharField("自定义 API 地址", max_length=255, null=True, blank=True)
    model = models.CharField("模型名称", max_length=100)
    is_default = models.BooleanField("默认", default=False)
    supports_vision = models.BooleanField("支持图片", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_model_configs"
        indexes = [models.Index(fields=["user", "is_default"])]
        verbose_name = verbose_name_plural = "AI 模型配置"

    def __str__(self):
        return f"{self.name} ({self.provider}/{self.model})"


class ChatSession(models.Model):
    """对应 Prisma 模型 ChatSession。"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField("标题", max_length=200, null=True, blank=True)
    summary = models.TextField("旧消息摘要", null=True, blank=True)
    summary_up_to = models.IntegerField("摘要覆盖到的消息序号", null=True, blank=True)
    ai_config = models.ForeignKey(AIModelConfig, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField("激活（软删除标记）", default=True)
    is_pinned = models.BooleanField("置顶", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-is_pinned", "-updated_at"]
        indexes = [
            models.Index(fields=["user", "updated_at"]),
            models.Index(fields=["user", "is_active"]),
        ]
        verbose_name = verbose_name_plural = "AI 会话"


class ChatMessage(models.Model):
    """对应 Prisma 模型 ChatMessage。"""

    ROLE_CHOICES = [("system", "system"), ("user", "user"), ("assistant", "assistant"), ("tool", "tool")]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    seq_num = models.IntegerField("会话内序号")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(null=True, blank=True)
    tool_calls = models.JSONField("工具调用", null=True, blank=True)
    tool_call_id = models.CharField(max_length=100, null=True, blank=True)
    tool_name = models.CharField(max_length=50, null=True, blank=True)
    tool_result = models.JSONField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["seq_num"]
        constraints = [models.UniqueConstraint(fields=["session", "seq_num"], name="uniq_session_seq")]
        verbose_name = verbose_name_plural = "AI 消息"
