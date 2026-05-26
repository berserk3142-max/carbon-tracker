from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.AuditLogViewSet, basename='audit')

urlpatterns = [
    path('record/<int:record_id>/', views.record_audit_trail, name='record-audit-trail'),
    path('', include(router.urls)),
]
