from django.urls import path

from . import views

urlpatterns = [
    path("check", views.CheckView.as_view()),
    path("latest", views.LatestView.as_view()),
]
