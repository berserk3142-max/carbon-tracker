from rest_framework import viewsets, permissions
from .models import Organization, Plant
from .serializers import OrganizationSerializer, PlantSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Tenant isolation: only see your own org
        return Organization.objects.filter(id=self.request.user.organization_id)


class PlantViewSet(viewsets.ModelViewSet):
    serializer_class = PlantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Plant.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
