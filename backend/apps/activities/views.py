"""
Activity views: Review queue, detail, approve/reject/edit, dashboard stats.
This is the main API that the analyst review dashboard consumes.
"""
import math
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ActivityRecord
from .serializers import (
    ActivityRecordListSerializer,
    ActivityRecordDetailSerializer,
    ReviewActionSerializer,
    ActivityEditSerializer,
)
from apps.audits.models import AuditLog
from apps.ingestion.models import DataSource


def safe_number(value):
    if value is None:
        return 0
    if isinstance(value, float) and not math.isfinite(value):
        return 0
    return value


def finite_co2e_sum(qs, scope=None):
    if scope is not None:
        qs = qs.filter(scope=scope)
    total = 0
    for value in qs.values_list('co2e_kg', flat=True).iterator():
        if isinstance(value, (int, float)) and math.isfinite(value):
            total += value
    return total


def safe_co2e_sum(value, qs, scope=None):
    if value is None:
        return 0
    if isinstance(value, float) and not math.isfinite(value):
        return finite_co2e_sum(qs, scope)
    return value


class ActivityRecordViewSet(viewsets.ModelViewSet):
    """
    Activity records — the core reviewable entities.

    Supports:
    - List with filtering (scope, status, suspicious, date range)
    - Detail view with raw record + audit trail
    - Approve/reject/lock actions
    - Edit (creates audit log, blocked if locked)
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['scope', 'status', 'suspicious', 'category', 'activity_type']
    search_fields = ['activity_type', 'description', 'plant_code', 'facility']
    ordering_fields = ['created_at', 'activity_date', 'co2e_kg', 'normalized_quantity', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ActivityRecordDetailSerializer
        if self.action in ('partial_update', 'update'):
            return ActivityEditSerializer
        return ActivityRecordListSerializer

    def get_queryset(self):
        qs = ActivityRecord.objects.filter(
            organization=self.request.user.organization
        )

        if self.action == 'retrieve':
            qs = qs.select_related('raw_record', 'emission_factor', 'reviewed_by', 'datasource')
        else:
            qs = qs.select_related('reviewed_by', 'datasource')

        # Custom date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(activity_date__gte=date_from)
        if date_to:
            qs = qs.filter(activity_date__lte=date_to)

        # Filter for review queue (pending + flagged)
        needs_review = self.request.query_params.get('needs_review')
        if needs_review == 'true':
            qs = qs.filter(status__in=['pending', 'flagged', 'validated'])

        return qs

    def perform_update(self, serializer):
        """Override update to create audit log and block locked records."""
        instance = self.get_object()

        if instance.locked:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This record is locked for audit. Cannot edit.")

        # Capture old values for audit
        old_values = {}
        for field in serializer.validated_data:
            old_val = getattr(instance, field)
            if hasattr(old_val, 'isoformat'):
                old_val = old_val.isoformat()
            old_values[field] = str(old_val) if old_val is not None else None

        # Save changes
        instance = serializer.save()

        # Capture new values
        new_values = {}
        for field in serializer.validated_data:
            new_val = getattr(instance, field)
            if hasattr(new_val, 'isoformat'):
                new_val = new_val.isoformat()
            new_values[field] = str(new_val) if new_val is not None else None

        # Create audit log
        AuditLog.objects.create(
            record=instance,
            action='updated',
            changed_by=self.request.user,
            old_values=old_values,
            new_values=new_values,
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an activity record."""
        record = self.get_object()

        if record.locked:
            return Response(
                {'error': 'Record is locked for audit.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = record.status
        record.status = 'approved'
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.reviewer_comment = serializer.validated_data.get('comment', '')
        record.suspicious = False
        record.save()

        AuditLog.objects.create(
            record=record,
            action='approved',
            changed_by=request.user,
            old_values={'status': old_status},
            new_values={'status': 'approved'},
            comment=record.reviewer_comment,
        )

        return Response(ActivityRecordDetailSerializer(record).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an activity record."""
        record = self.get_object()

        if record.locked:
            return Response(
                {'error': 'Record is locked for audit.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = record.status
        record.status = 'rejected'
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.reviewer_comment = serializer.validated_data.get('comment', '')
        record.save()

        AuditLog.objects.create(
            record=record,
            action='rejected',
            changed_by=request.user,
            old_values={'status': old_status},
            new_values={'status': 'rejected'},
            comment=record.reviewer_comment,
        )

        return Response(ActivityRecordDetailSerializer(record).data)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock a record for audit. Only approved records can be locked."""
        record = self.get_object()

        if record.status != 'approved':
            return Response(
                {'error': 'Only approved records can be locked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.locked = True
        record.locked_at = timezone.now()
        record.locked_by = request.user
        record.status = 'locked'
        record.save()

        AuditLog.objects.create(
            record=record,
            action='locked',
            changed_by=request.user,
            old_values={'locked': False, 'status': 'approved'},
            new_values={'locked': True, 'status': 'locked'},
        )

        return Response(ActivityRecordDetailSerializer(record).data)

    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        """Bulk approve multiple records."""
        record_ids = request.data.get('record_ids', [])
        comment = request.data.get('comment', '')

        if not record_ids:
            return Response(
                {'error': 'No record IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = list(ActivityRecord.objects.filter(
            id__in=record_ids,
            organization=request.user.organization,
            locked=False,
        ))

        now = timezone.now()
        audit_logs = []
        for record in records:
            old_status = record.status
            record.status = 'approved'
            record.reviewed_by = request.user
            record.reviewed_at = now
            record.reviewer_comment = comment
            record.suspicious = False
            audit_logs.append(
                AuditLog(
                    record=record,
                    action='approved',
                    changed_by=request.user,
                    old_values={'status': old_status},
                    new_values={'status': 'approved'},
                    comment=f'Bulk approved: {comment}',
                )
            )

        with transaction.atomic():
            ActivityRecord.objects.bulk_update(
                records,
                ['status', 'reviewed_by', 'reviewed_at', 'reviewer_comment', 'suspicious'],
            )
            AuditLog.objects.bulk_create(audit_logs)

        return Response({'approved': len(records)})

    @action(detail=False, methods=['post'])
    def bulk_lock(self, request):
        """Bulk lock approved records for audit."""
        record_ids = request.data.get('record_ids', [])

        records = list(ActivityRecord.objects.filter(
            id__in=record_ids,
            organization=request.user.organization,
            status='approved',
            locked=False,
        ))

        now = timezone.now()
        audit_logs = []
        for record in records:
            record.locked = True
            record.locked_at = now
            record.locked_by = request.user
            record.status = 'locked'
            audit_logs.append(
                AuditLog(
                    record=record,
                    action='locked',
                    changed_by=request.user,
                    old_values={'locked': False, 'status': 'approved'},
                    new_values={'locked': True, 'status': 'locked'},
                )
            )

        with transaction.atomic():
            ActivityRecord.objects.bulk_update(
                records,
                ['locked', 'locked_at', 'locked_by', 'status'],
            )
            AuditLog.objects.bulk_create(audit_logs)

        return Response({'locked': len(records)})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the current organization."""
    org = request.user.organization
    qs = ActivityRecord.objects.filter(organization=org)

    aggregates = qs.aggregate(
        total_records=Count('id'),
        pending_review=Count('id', filter=Q(status__in=['pending', 'validated'])),
        flagged=Count('id', filter=Q(status='flagged')),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected')),
        locked=Count('id', filter=Q(status='locked')),
        total_co2e_kg=Sum('co2e_kg'),
        scope_1_co2e=Sum('co2e_kg', filter=Q(scope=1)),
        scope_2_co2e=Sum('co2e_kg', filter=Q(scope=2)),
        scope_3_co2e=Sum('co2e_kg', filter=Q(scope=3)),
    )

    # Count recent uploads (last 7 days)
    from datetime import timedelta
    recent_cutoff = timezone.now() - timedelta(days=7)
    recent_uploads = DataSource.objects.filter(
        organization=org,
        uploaded_at__gte=recent_cutoff,
    ).count()

    stats = {
        'total_records': safe_number(aggregates['total_records']),
        'pending_review': safe_number(aggregates['pending_review']),
        'flagged': safe_number(aggregates['flagged']),
        'approved': safe_number(aggregates['approved']),
        'rejected': safe_number(aggregates['rejected']),
        'locked': safe_number(aggregates['locked']),
        'total_co2e_kg': safe_co2e_sum(aggregates['total_co2e_kg'], qs),
        'scope_1_co2e': safe_co2e_sum(aggregates['scope_1_co2e'], qs, 1),
        'scope_2_co2e': safe_co2e_sum(aggregates['scope_2_co2e'], qs, 2),
        'scope_3_co2e': safe_co2e_sum(aggregates['scope_3_co2e'], qs, 3),
        'recent_uploads': recent_uploads,
    }

    return Response(stats)
