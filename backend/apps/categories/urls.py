from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet

router = SimpleRouter(trailing_slash=False)
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = router.urls
