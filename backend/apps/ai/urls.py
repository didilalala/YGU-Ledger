from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter(trailing_slash=False)
router.register("configs", views.AIModelConfigViewSet, basename="ai-config")
router.register("chat/sessions", views.ChatSessionViewSet, basename="chat-session")

urlpatterns = [
    path("chat/send", views.ChatSendView.as_view()),
    path("chat/stream", views.chat_stream),
    path("asr/transcribe", views.AsrTranscribeView.as_view()),
    path("parse-bills", views.ParseBillsView.as_view()),
] + router.urls
