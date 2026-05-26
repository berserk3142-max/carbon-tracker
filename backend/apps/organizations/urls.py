from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.OrganizationViewSet, basename='organization')
router.register('plants', views.PlantViewSet, basename='plant')

urlpatterns = [
    path('', include(router.urls)),
]
