from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "icon", "color", "is_default", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "is_default", "created_at", "updated_at"]
