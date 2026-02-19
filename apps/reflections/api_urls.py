from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RetrospectiveViewSet

router = DefaultRouter()
router.register("retrospectives",RetrospectiveViewSet, basename="retrospective")

urlpatterns = router.urls