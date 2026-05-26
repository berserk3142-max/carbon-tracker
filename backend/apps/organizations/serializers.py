from rest_framework import serializers
from .models import Organization, Plant, AirportLookup


class OrganizationSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'industry', 'country', 'created_at', 'updated_at', 'user_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_count(self, obj):
        return obj.users.count()


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = ['id', 'code', 'name', 'location', 'country', 'created_at']
        read_only_fields = ['id', 'created_at']


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirportLookup
        fields = ['iata_code', 'name', 'city', 'country', 'latitude', 'longitude']
