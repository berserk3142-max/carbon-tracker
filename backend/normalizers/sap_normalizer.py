"""
SAP Fuel & Procurement Normalizer.

Handles realistic SAP CSV exports with German field names,
inconsistent units, and plant code lookups.

SAP field mapping:
  WERKS → plant_code (Plant)
  MATNR → material_number (Material)
  MENGE → quantity (Amount)
  MEINS → unit (Unit of Measure)
  BUDAT → posting_date (Posting Date)
  LIFNR → vendor (Vendor Number)
  BELNR → document_number (Document Number)
"""
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Column Mapping: German SAP headers → internal field names ───
SAP_COLUMN_MAP = {
    'WERKS': 'plant_code',
    'MATNR': 'material_number',
    'MENGE': 'quantity',
    'MEINS': 'unit',
    'BUDAT': 'posting_date',
    'LIFNR': 'vendor',
    'BELNR': 'document_number',
    # Alternative header formats
    'werks': 'plant_code',
    'matnr': 'material_number',
    'menge': 'quantity',
    'meins': 'unit',
    'budat': 'posting_date',
    'Plant': 'plant_code',
    'Material': 'material_number',
    'Quantity': 'quantity',
    'Unit': 'unit',
    'Posting Date': 'posting_date',
}

# ─── Unit Normalization: handles inconsistent unit formats ───
UNIT_NORMALIZATION = {
    # Liters
    'L': ('liters', 1.0),
    'l': ('liters', 1.0),
    'Liters': ('liters', 1.0),
    'liters': ('liters', 1.0),
    'LTR': ('liters', 1.0),
    'ltr': ('liters', 1.0),
    # Gallons → Liters
    'GAL': ('liters', 3.78541),
    'gal': ('liters', 3.78541),
    'Gallons': ('liters', 3.78541),
    # Kilograms
    'KG': ('kg', 1.0),
    'kg': ('kg', 1.0),
    'Kg': ('kg', 1.0),
    # Tons → Kilograms
    'TON': ('kg', 1000.0),
    'ton': ('kg', 1000.0),
    'Tons': ('kg', 1000.0),
    'MT': ('kg', 1000.0),
    't': ('kg', 1000.0),
    'T': ('kg', 1000.0),
    # Cubic meters (for natural gas)
    'M3': ('m3', 1.0),
    'm3': ('m3', 1.0),
    'CBM': ('m3', 1.0),
}

# ─── Material Code → Activity Classification ───
MATERIAL_TO_ACTIVITY = {
    'DSL-FUEL': {
        'activity_type': 'Diesel Combustion',
        'scope': 1,
        'category': 'stationary_combustion',
        'emission_activity': 'diesel_combustion',
        'fuel_type': 'diesel',
    },
    'PET-FUEL': {
        'activity_type': 'Petrol Combustion',
        'scope': 1,
        'category': 'mobile_combustion',
        'emission_activity': 'petrol_combustion',
        'fuel_type': 'petrol',
    },
    'COAL-01': {
        'activity_type': 'Coal Combustion',
        'scope': 1,
        'category': 'stationary_combustion',
        'emission_activity': 'coal_combustion',
        'fuel_type': 'coal',
    },
    'NAT-GAS': {
        'activity_type': 'Natural Gas Combustion',
        'scope': 1,
        'category': 'stationary_combustion',
        'emission_activity': 'natural_gas_combustion',
        'fuel_type': 'natural_gas',
    },
    'LPG-01': {
        'activity_type': 'LPG Combustion',
        'scope': 1,
        'category': 'stationary_combustion',
        'emission_activity': 'lpg_combustion',
        'fuel_type': 'lpg',
    },
    'HSD-FUEL': {
        'activity_type': 'High Speed Diesel',
        'scope': 1,
        'category': 'mobile_combustion',
        'emission_activity': 'diesel_combustion',
        'fuel_type': 'diesel',
    },
}


def map_columns(raw_payload: dict) -> dict:
    """Map SAP German headers to standard internal field names."""
    mapped = {}
    for key, value in raw_payload.items():
        internal_key = SAP_COLUMN_MAP.get(key, key.lower())
        mapped[internal_key] = value
    return mapped


def normalize_unit(unit_str: str, quantity: float) -> tuple:
    """
    Normalize unit to standard format and convert quantity.
    Returns (normalized_unit, normalized_quantity).
    """
    if not unit_str:
        return ('unknown', quantity)

    unit_str = unit_str.strip()
    if unit_str in UNIT_NORMALIZATION:
        norm_unit, factor = UNIT_NORMALIZATION[unit_str]
        return (norm_unit, quantity * factor)

    return (unit_str.lower(), quantity)


def classify_material(material_code: str) -> dict:
    """Classify material code into activity type, scope, and category."""
    material_code = material_code.strip().upper() if material_code else ''

    if material_code in MATERIAL_TO_ACTIVITY:
        return MATERIAL_TO_ACTIVITY[material_code]

    # Unknown material — flag for review
    return {
        'activity_type': f'Unknown Material ({material_code})',
        'scope': 1,
        'category': 'other',
        'emission_activity': 'unknown',
        'fuel_type': 'unknown',
    }


def parse_date(date_str: str):
    """Parse various date formats from SAP."""
    if not date_str:
        return None

    date_str = str(date_str).strip()
    formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',   # German format
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y%m%d',     # SAP compact format
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def normalize_row(raw_payload: dict, organization_id: int) -> dict:
    """
    Normalize a single SAP raw record into a standardized activity record.

    Returns a dict ready to create an ActivityRecord, plus any validation flags.
    """
    mapped = map_columns(raw_payload)
    flags = []

    # Extract fields
    material_code = str(mapped.get('material_number', '')).strip()
    plant_code = str(mapped.get('plant_code', '')).strip()
    raw_quantity = mapped.get('quantity', 0)
    raw_unit = str(mapped.get('unit', '')).strip()
    posting_date = mapped.get('posting_date', '')

    # Parse quantity
    try:
        quantity = float(raw_quantity)
        if not math.isfinite(quantity):
            raise ValueError('non-finite quantity')
    except (ValueError, TypeError):
        quantity = 0
        flags.append({
            'rule': 'invalid_quantity',
            'severity': 'error',
            'message': f'Cannot parse quantity: {raw_quantity}',
        })

    # Normalize unit
    normalized_unit, normalized_quantity = normalize_unit(raw_unit, quantity)
    if normalized_unit == 'unknown':
        flags.append({
            'rule': 'unknown_unit',
            'severity': 'warning',
            'message': f'Unknown unit: {raw_unit}',
        })

    # Classify material
    classification = classify_material(material_code)
    if classification['emission_activity'] == 'unknown':
        flags.append({
            'rule': 'unknown_material',
            'severity': 'warning',
            'message': f'Unknown material code: {material_code}. Cannot auto-classify.',
        })

    # Parse date
    activity_date = parse_date(posting_date)
    if not activity_date:
        flags.append({
            'rule': 'invalid_date',
            'severity': 'warning',
            'message': f'Cannot parse posting date: {posting_date}',
        })

    # Build normalized record
    record = {
        'organization_id': organization_id,
        'activity_type': classification['activity_type'],
        'scope': classification['scope'],
        'category': classification['category'],
        'quantity': quantity,
        'original_unit': raw_unit,
        'normalized_quantity': normalized_quantity,
        'normalized_unit': normalized_unit,
        'activity_date': activity_date,
        'plant_code': plant_code,
        'description': f"{classification['activity_type']} at plant {plant_code}",
        'suspicious_reasons': flags,
        'suspicious': len(flags) > 0,
        '_emission_activity': classification['emission_activity'],
        '_fuel_type': classification['fuel_type'],
    }

    return record
