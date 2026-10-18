from rest_framework.routers import SimpleRouter

from .views import BillViewSet

router = SimpleRouter(trailing_slash=False)
router.register("bills", BillViewSet, basename="bill")

urlpatterns = router.urls
