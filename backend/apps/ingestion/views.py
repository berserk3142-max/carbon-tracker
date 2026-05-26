"""
Ingestion views: file upload and data source management.
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import DataSource, RawRecord
from .serializers import (
    DataSourceListSerializer,
    DataSourceDetailSerializer,
    FileUploadSerializer,
    RawRecordSerializer,
)
from .services import process_upload


class DataSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve data sources (upload history)."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataSourceDetailSerializer
        return DataSourceListSerializer

    def get_queryset(self):
        qs = DataSource.objects.filter(
            organization=self.request.user.organization
        ).select_related('uploaded_by')
        if self.action == 'retrieve':
            qs = qs.prefetch_related('raw_records')
        return qs

    @action(detail=True, methods=['get'])
    def raw_records(self, request, pk=None):
        """Get raw records for a specific data source."""
        datasource = self.get_object()
        records = datasource.raw_records.all()
        serializer = RawRecordSerializer(records, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_file(request):
    """
    Upload a CSV file for processing.

    Expects multipart form data with:
    - file: CSV file
    - source_type: 'sap' | 'utility' | 'travel'
    """
    serializer = FileUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    file = serializer.validated_data['file']
    source_type = serializer.validated_data['source_type']

    # Create DataSource record
    datasource = DataSource.objects.create(
        organization=request.user.organization,
        source_type=source_type,
        ingestion_method='csv',
        file_name=file.name,
        uploaded_by=request.user,
        status='uploading',
    )

    # Read file content
    file_content = file.read()

    # Process the upload (synchronous for now — would use Celery in production)
    results = process_upload(datasource, file_content)

    # Refresh datasource from DB
    datasource.refresh_from_db()

    return Response({
        'datasource': DataSourceListSerializer(datasource).data,
        'results': results,
    }, status=status.HTTP_201_CREATED)
