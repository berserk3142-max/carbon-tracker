"""
Utility Electricity Normalizer.

Handles CSV exports from utility portals with:
- Non-monthly-aligned billing periods
- Mixed units (kWh / MWh)
- Multiple meters/facilities
- Tariff types

All electricity is classified as Scope 2.
"""
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Column Mapping: various utility CSV headers ───
UTILITY_COLUMN_MAP = {
    'meter_id': 'meter_id',
    'Meter ID': 'meter_id',
    'meter': 'meter_id',
    'facility': 'facility',
    'Facility': 'facility',
    'location': 'facility',
    'start_date': 'billing_start',
    'Start Date': 'billing_start',
    'billing_start': 'billing_start',
    'end_date': 'billing_end',
    'End Date': 'billing_end',
    'billing_end': 'billing_end',
    'usage_kwh': 'usage_kwh',
    'Usage (kWh)': 'usage_kwh',
    'kwh': 'usage_kwh',
    'usage_mwh': 'usage_mwh',
    'Usage (MWh)': 'usage_mwh',
    'mwh': 'usage_mwh',
    'cost': 'cost',
    'cost_usd': 'cost',
    'Cost': 'cost',
    'tariff_type': 'tariff_type',
    'Tariff': 'tariff_type',
    'tariff': 'tariff_type',
}

# ─── Unit normalization: everything to kWh ───
UNIT_CONVERSIONS = {
    'kwh': 1.0,
    'kWh': 1.0,
    'KWH': 1.0,
    'mwh': 1000.0,
    'MWh': 1000.0,
    'MWH': 1000.0,
    'gwh': 1_000_000.0,
    'GWh': 1_000_000.0,
}


def map_columns(raw_payload: dict) -> dict:
    """Map various utility CSV headers to standard internal names."""
    mapped = {}
    for key, value in raw_payload.items():
        internal_key = UTILITY_COLUMN_MAP.get(key, key.lower().replace(' ', '_'))
        mapped[internal_key] = value
    return mapped


def parse_date(date_str: str):
    """Parse various date formats from utility bills."""
    if not date_str:
        return None

    date_str = str(date_str).strip()
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%b %d, %Y',
        '%d %b %Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def normalize_row(raw_payload: dict, organization_id: int) -> dict:
    """
    Normalize a single utility record into a standardized activity record.

    Handles:
    - kWh vs MWh conversion
    - Billing period date parsing
    - Scope 2 classification
    """
    mapped = map_columns(raw_payload)
    flags = []

    # Extract fields
    meter_id = str(mapped.get('meter_id', '')).strip()
    facility = str(mapped.get('facility', '')).strip()
    billing_start = mapped.get('billing_start', '')
    billing_end = mapped.get('billing_end', '')
    tariff_type = str(mapped.get('tariff_type', 'standard')).strip()

    # Determine usage — prefer kWh, convert MWh if needed
    usage_kwh = mapped.get('usage_kwh', '')
    usage_mwh = mapped.get('usage_mwh', '')

    quantity = 0
    original_unit = 'kWh'
    normalized_quantity = 0

    try:
        if usage_kwh and str(usage_kwh).strip():
            quantity = float(usage_kwh)
            if not math.isfinite(quantity):
                raise ValueError('non-finite kWh value')
            original_unit = 'kWh'
            normalized_quantity = quantity
        elif usage_mwh and str(usage_mwh).strip():
            quantity = float(usage_mwh)
            if not math.isfinite(quantity):
                raise ValueError('non-finite MWh value')
            original_unit = 'MWh'
            normalized_quantity = quantity * 1000.0  # Convert to kWh
        else:
            flags.append({
                'rule': 'missing_usage',
                'severity': 'error',
                'message': 'No usage value found (neither kWh nor MWh)',
            })
    except (ValueError, TypeError):
        flags.append({
            'rule': 'invalid_usage',
            'severity': 'error',
            'message': f'Cannot parse usage value: kWh={usage_kwh}, MWh={usage_mwh}',
        })

    # Parse dates
    start_date = parse_date(billing_start)
    end_date = parse_date(billing_end)

    if not start_date:
        flags.append({
            'rule': 'invalid_start_date',
            'severity': 'warning',
            'message': f'Cannot parse billing start date: {billing_start}',
        })
    if not end_date:
        flags.append({
            'rule': 'invalid_end_date',
            'severity': 'warning',
            'message': f'Cannot parse billing end date: {billing_end}',
        })

    # Use end_date as the activity_date (when billing period closes)
    activity_date = end_date or start_date

    # Build description
    desc_parts = [f"Electricity usage at {facility}" if facility else "Electricity usage"]
    if meter_id:
        desc_parts.append(f"meter {meter_id}")
    if billing_start and billing_end:
        desc_parts.append(f"period {billing_start} to {billing_end}")
    if tariff_type:
        desc_parts.append(f"tariff: {tariff_type}")

    record = {
        'organization_id': organization_id,
        'activity_type': 'Purchased Electricity',
        'scope': 2,
        'category': 'purchased_electricity',
        'quantity': quantity,
        'original_unit': original_unit,
        'normalized_quantity': normalized_quantity,
        'normalized_unit': 'kWh',
        'activity_date': activity_date,
        'facility': facility,
        'description': ' | '.join(desc_parts),
        'suspicious_reasons': flags,
        'suspicious': len(flags) > 0,
        '_emission_activity': 'electricity',
        '_fuel_type': 'grid_electricity',
    }

    return record
