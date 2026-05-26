"""
ActivityRecord and EmissionFactor models.
ActivityRecord is the normalized, reviewable record at the heart of the system.
"""
from django.db import models


class EmissionFactor(models.Model):
    """
    Configurable emission factors table.
    Not hardcoded — auditors can verify the source and validity period.
    """
    activity_type = models.CharField(max_length=100, help_text="e.g. diesel_combustion, electricity, flight")
    fuel_type = models.CharField(max_length=100, blank=True, default='', help_text="e.g. diesel, coal, natural_gas")
    unit = models.CharField(max_length=50, help_text="Input unit e.g. liters, kWh, km")
    factor_value = models.FloatField(help_text="kg CO2e per unit")
    factor_unit = models.CharField(max_length=50, default='kg_co2e', help_text="Output unit")
    source = models.CharField(max_length=255, help_text="e.g. DEFRA 2025, EPA GHG Hub")
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emission_factors'
        ordering = ['activity_type', 'fuel_type']

    def __str__(self):
        return f"{self.activity_type}/{self.fuel_type}: {self.factor_value} {self.factor_unit}/{self.unit}"


class ActivityRecord(models.Model):
    """
    Normalized activity record — the core reviewable entity.
    Links back to RawRecord for traceability.
    Supports the full review lifecycle: pending → flagged → approved → locked.
    """
    SCOPE_CHOICES = [
        (1, 'Scope 1 — Direct Emissions'),
        (2, 'Scope 2 — Purchased Electricity'),
        (3, 'Scope 3 — Indirect (Travel/Procurement)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('validated', 'Validated'),
        ('flagged', 'Flagged for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked for Audit'),
    ]

    CATEGORY_CHOICES = [
        ('stationary_combustion', 'Stationary Combustion'),
        ('mobile_combustion', 'Mobile Combustion'),
        ('purchased_electricity', 'Purchased Electricity'),
        ('business_travel', 'Business Travel'),
        ('employee_commuting', 'Employee Commuting'),
        ('procurement', 'Procurement'),
        ('other', 'Other'),
    ]

    # Traceability
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='activities',
    )
    raw_record = models.OneToOneField(
        'ingestion.RawRecord',
        on_delete=models.CASCADE,
        related_name='activity',
        null=True,
        blank=True,
    )
    datasource = models.ForeignKey(
        'ingestion.DataSource',
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True,
    )

    # Activity classification
    activity_type = models.CharField(max_length=100, help_text="e.g. Diesel Combustion, Electricity, Flight")
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Quantities — original and normalized
    quantity = models.FloatField(help_text="Original quantity from source")
    original_unit = models.CharField(max_length=50, help_text="Unit as reported in source")
    normalized_quantity = models.FloatField(help_text="Quantity after unit normalization")
    normalized_unit = models.CharField(max_length=50, help_text="Standard unit after normalization")

    # Emissions
    emission_factor = models.ForeignKey(
        EmissionFactor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )
    emission_factor_value = models.FloatField(null=True, blank=True, help_text="Snapshot of factor used")
    co2e_kg = models.FloatField(null=True, blank=True, help_text="Calculated CO2 equivalent in kg")

    # Metadata
    activity_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    plant_code = models.CharField(max_length=20, blank=True, default='')
    facility = models.CharField(max_length=255, blank=True, default='')

    # Review workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    suspicious = models.BooleanField(default=False)
    suspicious_reasons = models.JSONField(default=list, blank=True, help_text="List of validation flags")

    # Review actions
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_activities',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_comment = models.TextField(blank=True, default='')

    # Audit lock
    locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_activities',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'activity_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'scope']),
            models.Index(fields=['organization', 'suspicious']),
            models.Index(fields=['status', 'suspicious']),
        ]

    def __str__(self):
        return f"{self.activity_type} | Scope {self.scope} | {self.normalized_quantity} {self.normalized_unit} | {self.status}"
