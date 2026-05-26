"""
AuditLog model — Full change tracking for auditability.
Every change to an ActivityRecord is logged with old/new values.
Auditors LOVE this.
"""
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail for all ActivityRecord changes.
    Stores old and new values as JSONB for any field change.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
        ('comment', 'Comment Added'),
    ]

    record = models.ForeignKey(
        'activities.ActivityRecord',
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
    )
    old_values = models.JSONField(default=dict, blank=True, help_text="Field values before change")
    new_values = models.JSONField(default=dict, blank=True, help_text="Field values after change")
    comment = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['record', '-timestamp']),
        ]

    def __str__(self):
        return f"Audit: {self.action} on Record#{self.record_id} by {self.changed_by} at {self.timestamp}"
