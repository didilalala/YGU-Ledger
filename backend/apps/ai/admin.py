from django.contrib import admin

from .models import AIModelConfig, ChatMessage, ChatSession


@admin.register(AIModelConfig)
class AIModelConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "model", "user", "is_default"]
    list_filter = ["provider"]
    exclude = ["api_key"]


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ["seq_num", "role", "content", "tool_name"]
    readonly_fields = fields


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "user", "is_pinned", "is_active", "updated_at"]
    inlines = [ChatMessageInline]
