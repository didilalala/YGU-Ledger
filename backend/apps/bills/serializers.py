from decimal import Decimal

from rest_framework import serializers

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer

from .models import Bill


class BillSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=4, coerce_to_string=False, min_value=Decimal("0"))
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), required=False, allow_null=True)
    account_id = serializers.PrimaryKeyRelatedField(
        source="account", queryset=Account.objects.all(), required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=30), required=False)

    class Meta:
        model = Bill
        fields = ["id", "amount", "type", "description", "date", "time", "category", "category_id",
                  "account_id", "tags", "notes", "receipt_url", "source", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_category_id(self, category):
        user = self.context["request"].user
        if category and category.user_id not in (None, user.id):
            raise serializers.ValidationError("分类不存在")
        return category

    def validate_account_id(self, account):
        if account and account.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("账户不存在")
        return account


class BillQuerySerializer(serializers.Serializer):
    """列表查询参数，对应原项目 query-bill.dto.ts。"""

    type = serializers.ChoiceField(choices=["income", "expense"], required=False)
    category_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    order_by = serializers.ChoiceField(choices=["date", "amount", "created_at"], default="date")
    order_direction = serializers.ChoiceField(choices=["asc", "desc"], default="desc")


class StatisticsQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    granularity = serializers.ChoiceField(choices=["daily", "monthly"], default="daily")
