from rest_framework import serializers

from common.fields import mask_secret

from .models import AIModelConfig, ChatMessage, ChatSession


class AIModelConfigSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True)
    api_key_masked = serializers.SerializerMethodField()

    class Meta:
        model = AIModelConfig
        fields = ["id", "name", "provider", "api_key", "api_key_masked", "api_base_url", "model",
                  "is_default", "supports_vision", "created_at", "updated_at"]
        read_only_fields = ["id", "is_default", "created_at", "updated_at"]

    def get_api_key_masked(self, obj) -> str:
        return mask_secret(obj.api_key)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "seq_num", "role", "content", "tool_calls", "tool_call_id", "tool_name",
                  "tool_result", "image_url", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    ai_config_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "ai_config_id", "is_pinned", "created_at", "updated_at"]
        read_only_fields = ["id", "ai_config_id", "is_pinned", "created_at", "updated_at"]


class ChatSessionDetailSerializer(ChatSessionSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta(ChatSessionSerializer.Meta):
        fields = ChatSessionSerializer.Meta.fields + ["messages"]


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=True)
    session_id = serializers.IntegerField(required=False, allow_null=True)
    ai_config_id = serializers.IntegerField(required=False, allow_null=True)
    images = serializers.ListField(child=serializers.CharField(), required=False,
                                   help_text="Base64 图片列表")

    def validate(self, attrs):
        if not attrs.get("message", "").strip() and not attrs.get("images"):
            raise serializers.ValidationError("消息内容不能为空")
        return attrs


class AsrRequestSerializer(serializers.Serializer):
    audio = serializers.CharField(help_text="Base64 音频")
    mime_type = serializers.CharField(default="audio/mp4")
