from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet

router = DefaultRouter()
router.register(r"materiais", MaterialViewSet, basename="material")

urlpatterns = [
    path("api/", include(router.urls)),
]
