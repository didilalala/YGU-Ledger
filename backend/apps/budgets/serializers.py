from decimal import Decimal

from rest_framework import serializers

from apps.categories.models import Category

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=4, coerce_to_string=False, min_value=Decimal("0"))
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), required=False, allow_null=True)
    alert_at = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = Budget
        fields = ["id", "name", "amount", "period", "category_id", "alert_at", "is_active",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_category_id(self, category):
        if category and category.user_id not in (None, self.context["request"].user.id):
            raise serializers.ValidationError("分类不存在")
        return category
