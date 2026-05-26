from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('sources', views.DataSourceViewSet, basename='datasource')

urlpatterns = [
    path('upload/', views.upload_file, name='upload-file'),
    path('', include(router.urls)),
]
