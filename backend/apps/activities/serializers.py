"""
Activity serializers for the review workflow.
"""
import math
from rest_framework import serializers
from .models import ActivityRecord, EmissionFactor
from apps.ingestion.serializers import RawRecordSerializer


def json_safe_numbers(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe_numbers(item) for item in value]
    return value


class JsonSafeNumberMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return json_safe_numbers(data)


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = [
            'id', 'activity_type', 'fuel_type', 'unit',
            'factor_value', 'factor_unit', 'source',
            'valid_from', 'valid_to',
        ]


class ActivityRecordListSerializer(JsonSafeNumberMixin, serializers.ModelSerializer):
    """Lightweight serializer for the review queue table."""
    reviewed_by_name = serializers.SerializerMethodField()
    datasource_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityRecord
        fields = [
            'id', 'activity_type', 'scope', 'category',
            'quantity', 'original_unit',
            'normalized_quantity', 'normalized_unit',
            'co2e_kg', 'activity_date',
            'status', 'suspicious', 'suspicious_reasons',
            'plant_code', 'facility', 'description',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'reviewer_comment', 'locked',
            'datasource', 'datasource_name',
            'created_at', 'updated_at',
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return None

    def get_datasource_name(self, obj):
        if obj.datasource:
            return obj.datasource.file_name
        return None


class ActivityRecordDetailSerializer(JsonSafeNumberMixin, serializers.ModelSerializer):
    """Full detail serializer with nested raw record and emission factor."""
    raw_record = RawRecordSerializer(read_only=True)
    emission_factor_detail = EmissionFactorSerializer(source='emission_factor', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    datasource_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityRecord
        fields = [
            'id', 'activity_type', 'scope', 'category',
            'quantity', 'original_unit',
            'normalized_quantity', 'normalized_unit',
            'emission_factor_value', 'co2e_kg',
            'activity_date', 'description',
            'plant_code', 'facility',
            'status', 'suspicious', 'suspicious_reasons',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'reviewer_comment',
            'locked', 'locked_at',
            'raw_record', 'emission_factor_detail',
            'datasource', 'datasource_name',
            'created_at', 'updated_at',
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return None

    def get_datasource_name(self, obj):
        if obj.datasource:
            return obj.datasource.file_name
        return None


class ReviewActionSerializer(serializers.Serializer):
    """For approve/reject actions."""
    comment = serializers.CharField(required=False, default='', allow_blank=True)


class ActivityEditSerializer(serializers.ModelSerializer):
    """For editing activity records (before locking)."""
    class Meta:
        model = ActivityRecord
        fields = [
            'activity_type', 'scope', 'category',
            'normalized_quantity', 'normalized_unit',
            'co2e_kg', 'activity_date', 'description',
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics."""
    total_records = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    flagged = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    locked = serializers.IntegerField()
    total_co2e_kg = serializers.FloatField()
    scope_1_co2e = serializers.FloatField()
    scope_2_co2e = serializers.FloatField()
    scope_3_co2e = serializers.FloatField()
    recent_uploads = serializers.IntegerField()
