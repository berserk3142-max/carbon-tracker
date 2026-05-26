"""
Validation Engine — Flags suspicious and invalid records.

Runs a set of configurable validation rules against ActivityRecords.
This is exactly what ESG analysts do: catch anomalies before they
become audit problems.

Rules:
1. Negative quantities
2. Zero quantities
3. Missing/unknown units
4. Suspicious spikes (>5x category average)
5. Future dates
6. Extremely high values
"""
import logging
import math
from datetime import date
from django.db.models import Avg

logger = logging.getLogger(__name__)


class ValidationRule:
    """Base class for validation rules."""
    name = 'base_rule'
    severity = 'warning'

    def check(self, record_data: dict, context: dict = None) -> list:
        """
        Check the record against this rule.
        Returns a list of flag dicts: [{rule, severity, message}]
        """
        raise NotImplementedError


class NegativeQuantityRule(ValidationRule):
    name = 'negative_quantity'
    severity = 'error'

    def check(self, record_data, context=None):
        qty = record_data.get('normalized_quantity', 0)
        if qty < 0:
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': f'Negative quantity detected: {qty}. This may indicate a return/reversal or data error.',
            }]
        return []


class NonFiniteQuantityRule(ValidationRule):
    name = 'non_finite_quantity'
    severity = 'error'

    def check(self, record_data, context=None):
        qty = record_data.get('normalized_quantity', 0)
        if isinstance(qty, float) and not math.isfinite(qty):
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': 'Quantity is not a finite number. Check for blank, NaN, or infinite source values.',
            }]
        return []


class ZeroQuantityRule(ValidationRule):
    name = 'zero_quantity'
    severity = 'warning'

    def check(self, record_data, context=None):
        qty = record_data.get('normalized_quantity', 0)
        if qty == 0:
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': 'Zero quantity — verify this is not a data entry error.',
            }]
        return []


class MissingUnitRule(ValidationRule):
    name = 'missing_unit'
    severity = 'error'

    def check(self, record_data, context=None):
        unit = record_data.get('normalized_unit', '')
        if not unit or unit in ('unknown', ''):
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': f'Missing or unknown unit: "{record_data.get("original_unit", "")}". Cannot calculate emissions.',
            }]
        return []


class FutureDateRule(ValidationRule):
    name = 'future_date'
    severity = 'warning'

    def check(self, record_data, context=None):
        activity_date = record_data.get('activity_date')
        if activity_date and activity_date > date.today():
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': f'Activity date {activity_date} is in the future.',
            }]
        return []


class SuspiciousSpikeRule(ValidationRule):
    """
    Flags values that are >5x the average for the same activity type + org.
    This catches data entry errors like extra zeros.
    """
    name = 'suspicious_spike'
    severity = 'warning'

    def check(self, record_data, context=None):
        if not context or 'category_avg' not in context:
            return []

        qty = record_data.get('normalized_quantity', 0)
        avg = context.get('category_avg', 0)

        if avg > 0 and qty > avg * 5:
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': f'Quantity {qty} is {qty/avg:.1f}x the category average ({avg:.1f}). Possible data entry error.',
            }]
        return []


class ExtremeValueRule(ValidationRule):
    """Flags quantities that are unreasonably large."""
    name = 'extreme_value'
    severity = 'warning'

    # Thresholds per unit type
    THRESHOLDS = {
        'liters': 100000,    # 100k liters per single entry
        'kg': 500000,        # 500 tonnes per single entry
        'kWh': 1000000,      # 1 GWh per single entry
        'passenger-km': 50000,  # 50k km per trip
        'm3': 100000,        # 100k cubic meters
    }

    def check(self, record_data, context=None):
        qty = abs(record_data.get('normalized_quantity', 0))
        unit = record_data.get('normalized_unit', '')

        threshold = self.THRESHOLDS.get(unit)
        if threshold and qty > threshold:
            return [{
                'rule': self.name,
                'severity': self.severity,
                'message': f'Extreme value: {qty} {unit} exceeds expected maximum of {threshold} {unit}.',
            }]
        return []


# ─── Validation Engine ───

# All rules, executed in order
ALL_RULES = [
    NonFiniteQuantityRule(),
    NegativeQuantityRule(),
    ZeroQuantityRule(),
    MissingUnitRule(),
    FutureDateRule(),
    SuspiciousSpikeRule(),
    ExtremeValueRule(),
]


def validate_record(record_data: dict, context: dict = None) -> list:
    """
    Run all validation rules against a record.
    Returns a list of all flags found.
    """
    all_flags = []

    for rule in ALL_RULES:
        try:
            flags = rule.check(record_data, context)
            all_flags.extend(flags)
        except Exception as e:
            logger.error(f"Validation rule {rule.name} failed: {e}")
            all_flags.append({
                'rule': rule.name,
                'severity': 'info',
                'message': f'Validation rule error: {str(e)}',
            })

    return all_flags


def get_category_averages(organization_id: int) -> dict:
    """
    Calculate average quantities per activity_type for spike detection.
    Uses existing approved/validated records as baseline.
    """
    from apps.activities.models import ActivityRecord

    averages = {}
    qs = ActivityRecord.objects.filter(
        organization_id=organization_id,
        status__in=['validated', 'approved', 'locked'],
    ).values('activity_type', 'normalized_unit').annotate(
        avg_qty=Avg('normalized_quantity')
    )

    for row in qs:
        key = f"{row['activity_type']}_{row['normalized_unit']}"
        averages[key] = row['avg_qty']

    return averages
