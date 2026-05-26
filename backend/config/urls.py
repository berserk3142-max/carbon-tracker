"""
URL Configuration for ESG Carbon Accounting Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/ingestion/', include('apps.ingestion.urls')),
    path('api/activities/', include('apps.activities.urls')),
    path('api/audits/', include('apps.audits.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
