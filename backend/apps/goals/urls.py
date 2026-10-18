from rest_framework.routers import SimpleRouter

from .views import FinancialGoalViewSet

router = SimpleRouter(trailing_slash=False)
router.register("financial-goals", FinancialGoalViewSet, basename="financial-goal")

urlpatterns = router.urls
