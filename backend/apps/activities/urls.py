from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.ActivityRecordViewSet, basename='activity')

urlpatterns = [
    path('stats/', views.dashboard_stats, name='dashboard-stats'),
    path('', include(router.urls)),
]
