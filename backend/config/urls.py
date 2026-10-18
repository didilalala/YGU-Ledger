from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_patterns = [
    path("auth/", include("apps.users.urls")),
    # 以下 ViewSet 的路由前缀在各自 urls.py 中注册（如 bills、bills/<id>、bills/statistics）
    path("", include("apps.categories.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.bills.urls")),
    path("", include("apps.budgets.urls")),
    path("", include("apps.goals.urls")),
    path("ai/", include("apps.ai.urls")),
    path("app-version/", include("apps.versions.urls")),
    # 接口文档
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
