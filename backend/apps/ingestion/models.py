"""
Ingestion models — DataSource and RawRecord.
Tracks where data came from and stores immutable raw payloads.
"""
from django.db import models


class DataSource(models.Model):
    """
    Tracks every file/data upload into the system.
    Auditors need to know: where did this row come from? When? From which file?
    """
    SOURCE_TYPE_CHOICES = [
        ('sap', 'SAP Fuel & Procurement'),
        ('utility', 'Utility Electricity'),
        ('travel', 'Travel & Expenses'),
    ]

    INGESTION_METHOD_CHOICES = [
        ('csv', 'CSV Upload'),
        ('api', 'API Integration'),
        ('manual', 'Manual Entry'),
    ]

    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('parsing', 'Parsing'),
        ('normalizing', 'Normalizing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='data_sources',
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    ingestion_method = models.CharField(max_length=20, choices=INGESTION_METHOD_CHOICES, default='csv')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/%Y/%m/', null=True, blank=True)
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploads',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_summary = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'data_sources'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} ({self.source_type}) — {self.status}"


class RawRecord(models.Model):
    """
    Immutable raw record exactly as it came from the source.
    NEVER mutate this data — it's the audit-safe source of truth.
    """
    INGESTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('parsed', 'Parsed'),
        ('normalized', 'Normalized'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='raw_records',
    )
    row_number = models.IntegerField(help_text="Row number in the source file (1-indexed)")
    raw_payload = models.JSONField(help_text="Exact JSON representation of the source row")
    ingestion_status = models.CharField(max_length=20, choices=INGESTION_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'raw_records'
        ordering = ['datasource', 'row_number']
        indexes = [
            models.Index(fields=['datasource', 'ingestion_status']),
        ]

    def __str__(self):
        return f"Raw#{self.id} (Source:{self.datasource_id}, Row:{self.row_number})"
