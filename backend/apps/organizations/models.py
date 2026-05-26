"""
Organization model — Multi-tenant root entity.
One company = one tenant. All data is scoped to an organization.
"""
from django.db import models


class Organization(models.Model):
    """
    Represents a company/tenant in the system.
    Breathe ESG serves multiple clients — each is an Organization.
    """
    INDUSTRY_CHOICES = [
        ('manufacturing', 'Manufacturing'),
        ('energy', 'Energy & Utilities'),
        ('logistics', 'Logistics & Transportation'),
        ('technology', 'Technology'),
        ('finance', 'Financial Services'),
        ('healthcare', 'Healthcare'),
        ('retail', 'Retail'),
        ('construction', 'Construction'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, default='manufacturing')
    country = models.CharField(max_length=100, default='India')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def __str__(self):
        return self.name


class Plant(models.Model):
    """
    SAP Plant lookup table.
    Maps plant codes (WERKS) to physical locations.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='plants')
    code = models.CharField(max_length=20, help_text="SAP plant code e.g. 1102")
    name = models.CharField(max_length=255, help_text="e.g. Berlin Manufacturing Plant")
    location = models.CharField(max_length=255, help_text="City/region")
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'plants'
        unique_together = ['organization', 'code']
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name} ({self.location})"


class AirportLookup(models.Model):
    """
    Airport IATA code lookup for flight distance calculation.
    Used by the travel normalizer to estimate km from origin/destination codes.
    """
    iata_code = models.CharField(max_length=3, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'airport_lookup'
        ordering = ['iata_code']

    def __str__(self):
        return f"{self.iata_code} — {self.city}, {self.country}"
