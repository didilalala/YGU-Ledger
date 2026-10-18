from rest_framework import serializers

from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=15, decimal_places=4, coerce_to_string=False, required=False)

    class Meta:
        model = Account
        fields = ["id", "name", "type", "balance", "icon", "color", "is_default", "sort_order",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
