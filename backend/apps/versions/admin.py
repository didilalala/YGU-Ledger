from django.contrib import admin

from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ["version", "version_code", "platform", "force_update", "created_at"]
    list_filter = ["platform"]
