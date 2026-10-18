from decimal import Decimal

from rest_framework import serializers

from .models import FinancialGoal


class FinancialGoalSerializer(serializers.ModelSerializer):
    target_amount = serializers.DecimalField(max_digits=15, decimal_places=4, coerce_to_string=False, min_value=Decimal("0"))
    current_amount = serializers.DecimalField(max_digits=15, decimal_places=4, coerce_to_string=False,
                                              min_value=Decimal("0"), required=False)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = FinancialGoal
        fields = ["id", "name", "target_amount", "current_amount", "deadline", "icon", "color",
                  "is_completed", "progress", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_progress(self, obj) -> float:
        if not obj.target_amount:
            return 0
        return round(min(float(obj.current_amount / obj.target_amount * 100), 100), 1)
