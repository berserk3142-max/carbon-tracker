"""
Ingestion serializers for file upload and data source tracking.
"""
from rest_framework import serializers
from .models import DataSource, RawRecord


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = [
            'id', 'row_number', 'raw_payload',
            'ingestion_status', 'error_message', 'created_at',
        ]


class DataSourceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing uploads."""
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = [
            'id', 'source_type', 'ingestion_method', 'file_name',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'status', 'total_rows', 'processed_rows', 'failed_rows',
            'error_summary',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return 'Unknown'


class DataSourceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with raw records."""
    uploaded_by_name = serializers.SerializerMethodField()
    raw_records = RawRecordSerializer(many=True, read_only=True)

    class Meta:
        model = DataSource
        fields = [
            'id', 'source_type', 'ingestion_method', 'file_name',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'status', 'total_rows', 'processed_rows', 'failed_rows',
            'error_summary', 'raw_records',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return 'Unknown'


class FileUploadSerializer(serializers.Serializer):
    """Validates file upload requests."""
    file = serializers.FileField()
    source_type = serializers.ChoiceField(choices=DataSource.SOURCE_TYPE_CHOICES)

    def validate_file(self, value):
        # Check file extension
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are supported.")

        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 10MB.")

        return value
