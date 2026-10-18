from django.contrib import admin

from .models import FinancialGoal


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ["name", "target_amount", "current_amount", "deadline", "user"]
