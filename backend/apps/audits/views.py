"""
Audit log views.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve audit logs."""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action', 'record']
    ordering = ['-timestamp']

    def get_queryset(self):
        return AuditLog.objects.filter(
            record__organization=self.request.user.organization
        ).select_related('changed_by', 'record')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def record_audit_trail(request, record_id):
    """Get the full audit trail for a specific activity record."""
    logs = AuditLog.objects.filter(
        record_id=record_id,
        record__organization=request.user.organization,
    ).select_related('changed_by').order_by('-timestamp')

    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)
