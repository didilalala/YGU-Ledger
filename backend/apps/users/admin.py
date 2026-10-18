from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "nickname", "email", "is_active", "created_at"]
    search_fields = ["username", "nickname", "email"]
    readonly_fields = ["id", "password", "last_login", "created_at", "updated_at"]
