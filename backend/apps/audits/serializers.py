import math
from rest_framework import serializers
from .models import AuditLog


def json_safe_numbers(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe_numbers(item) for item in value]
    return value


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'record', 'action', 'changed_by',
            'changed_by_name', 'old_values', 'new_values',
            'comment', 'timestamp', 'ip_address',
        ]

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.username
        return 'System'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return json_safe_numbers(data)
