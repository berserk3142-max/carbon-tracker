"""
Travel & Expense Normalizer.

Handles CSV exports resembling Concur/Navan travel expense systems.
Key feature: Haversine distance calculation for flights using airport lookups.

All travel is classified as Scope 3 (Business Travel).
"""
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Column Mapping ───
TRAVEL_COLUMN_MAP = {
    'employee_id': 'employee_id',
    'Employee ID': 'employee_id',
    'employee_name': 'employee_name',
    'Employee': 'employee_name',
    'employee': 'employee_name',
    'travel_type': 'travel_type',
    'Travel Type': 'travel_type',
    'type': 'travel_type',
    'origin': 'origin',
    'Origin': 'origin',
    'from': 'origin',
    'From': 'origin',
    'destination': 'destination',
    'Destination': 'destination',
    'to': 'destination',
    'To': 'destination',
    'date': 'travel_date',
    'Date': 'travel_date',
    'travel_date': 'travel_date',
    'cost': 'cost',
    'Cost': 'cost',
    'amount': 'cost',
    'currency': 'currency',
    'Currency': 'currency',
    'purpose': 'purpose',
    'Purpose': 'purpose',
}

# ─── Travel type classification ───
TRAVEL_TYPE_MAP = {
    'flight': {'activity_type': 'Business Flight', 'category': 'business_travel'},
    'air': {'activity_type': 'Business Flight', 'category': 'business_travel'},
    'train': {'activity_type': 'Business Train', 'category': 'business_travel'},
    'rail': {'activity_type': 'Business Train', 'category': 'business_travel'},
    'hotel': {'activity_type': 'Hotel Stay', 'category': 'business_travel'},
    'accommodation': {'activity_type': 'Hotel Stay', 'category': 'business_travel'},
    'taxi': {'activity_type': 'Taxi/Cab', 'category': 'business_travel'},
    'cab': {'activity_type': 'Taxi/Cab', 'category': 'business_travel'},
    'car': {'activity_type': 'Car Rental', 'category': 'business_travel'},
    'bus': {'activity_type': 'Bus Travel', 'category': 'business_travel'},
}

# ─── Pre-loaded airport coordinates (major Indian + global airports) ───
# This gets supplemented from the DB at runtime
DEFAULT_AIRPORTS = {
    'DEL': {'lat': 28.5665, 'lon': 77.1031, 'city': 'Delhi'},
    'BLR': {'lat': 13.1989, 'lon': 77.7069, 'city': 'Bengaluru'},
    'BOM': {'lat': 19.0896, 'lon': 72.8656, 'city': 'Mumbai'},
    'MAA': {'lat': 12.9941, 'lon': 80.1709, 'city': 'Chennai'},
    'CCU': {'lat': 22.6547, 'lon': 88.4467, 'city': 'Kolkata'},
    'HYD': {'lat': 17.2403, 'lon': 78.4294, 'city': 'Hyderabad'},
    'COK': {'lat': 10.1520, 'lon': 76.4019, 'city': 'Kochi'},
    'PNQ': {'lat': 18.5822, 'lon': 73.9197, 'city': 'Pune'},
    'AMD': {'lat': 23.0771, 'lon': 72.6347, 'city': 'Ahmedabad'},
    'GOI': {'lat': 15.3808, 'lon': 73.8314, 'city': 'Goa'},
    'JAI': {'lat': 26.8242, 'lon': 75.8122, 'city': 'Jaipur'},
    'LKO': {'lat': 26.7606, 'lon': 80.8893, 'city': 'Lucknow'},
    'SXR': {'lat': 33.9871, 'lon': 74.7742, 'city': 'Srinagar'},
    # International
    'LHR': {'lat': 51.4700, 'lon': -0.4543, 'city': 'London'},
    'JFK': {'lat': 40.6413, 'lon': -73.7781, 'city': 'New York'},
    'SFO': {'lat': 37.6213, 'lon': -122.3790, 'city': 'San Francisco'},
    'SIN': {'lat': 1.3644, 'lon': 103.9915, 'city': 'Singapore'},
    'DXB': {'lat': 25.2532, 'lon': 55.3657, 'city': 'Dubai'},
    'FRA': {'lat': 50.0379, 'lon': 8.5622, 'city': 'Frankfurt'},
    'NRT': {'lat': 35.7720, 'lon': 140.3929, 'city': 'Tokyo'},
    'SYD': {'lat': -33.9461, 'lon': 151.1772, 'city': 'Sydney'},
    'CDG': {'lat': 49.0097, 'lon': 2.5479, 'city': 'Paris'},
    'MUC': {'lat': 48.3538, 'lon': 11.7861, 'city': 'Munich'},
    'TXL': {'lat': 52.5597, 'lon': 13.2877, 'city': 'Berlin'},
    'BER': {'lat': 52.3667, 'lon': 13.5033, 'city': 'Berlin'},
}

# Average train distances for common routes (km)
TRAIN_ROUTES = {
    ('berlin', 'munich'): 585,
    ('munich', 'berlin'): 585,
    ('delhi', 'mumbai'): 1384,
    ('mumbai', 'delhi'): 1384,
    ('delhi', 'kolkata'): 1530,
    ('kolkata', 'delhi'): 1530,
    ('london', 'paris'): 460,
    ('paris', 'london'): 460,
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def get_airport_coords(code: str, db_airports: dict = None) -> dict:
    """Look up airport coordinates from DB first, then fallback to defaults."""
    code = code.strip().upper()

    if db_airports and code in db_airports:
        return db_airports[code]

    if code in DEFAULT_AIRPORTS:
        return DEFAULT_AIRPORTS[code]

    return None


def calculate_flight_distance(origin: str, destination: str, db_airports: dict = None) -> tuple:
    """
    Calculate flight distance between two airports.
    Returns (distance_km, origin_city, destination_city) or (None, None, None).
    """
    origin_data = get_airport_coords(origin, db_airports)
    dest_data = get_airport_coords(destination, db_airports)

    if not origin_data or not dest_data:
        return None, origin, destination

    distance = haversine_distance(
        origin_data['lat'], origin_data['lon'],
        dest_data['lat'], dest_data['lon'],
    )

    return distance, origin_data['city'], dest_data['city']


def map_columns(raw_payload: dict) -> dict:
    """Map travel CSV headers to standard internal names."""
    mapped = {}
    for key, value in raw_payload.items():
        internal_key = TRAVEL_COLUMN_MAP.get(key, key.lower().replace(' ', '_'))
        mapped[internal_key] = value
    return mapped


def parse_date(date_str: str):
    """Parse travel date."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def normalize_row(raw_payload: dict, organization_id: int, db_airports: dict = None) -> dict:
    """
    Normalize a single travel record into a standardized activity record.

    Handles:
    - Travel type classification (flight/train/hotel/taxi)
    - Flight distance calculation via Haversine
    - Train distance lookup
    - Scope 3 classification
    """
    mapped = map_columns(raw_payload)
    flags = []

    # Extract fields
    travel_type = str(mapped.get('travel_type', '')).strip().lower()
    origin = str(mapped.get('origin', '')).strip()
    destination = str(mapped.get('destination', '')).strip()
    travel_date = mapped.get('travel_date', '')
    employee_name = str(mapped.get('employee_name', '')).strip()
    purpose = str(mapped.get('purpose', '')).strip()

    # Cost
    try:
        cost = float(mapped.get('cost', 0) or 0)
        if not math.isfinite(cost):
            raise ValueError('non-finite cost')
    except (ValueError, TypeError):
        cost = 0

    currency = str(mapped.get('currency', 'INR')).strip()

    # Classify travel type
    classification = TRAVEL_TYPE_MAP.get(travel_type, {
        'activity_type': f'Other Travel ({travel_type})',
        'category': 'business_travel',
    })

    # Calculate distance/quantity based on travel type
    quantity = 0
    original_unit = 'trip'
    normalized_quantity = 0
    normalized_unit = 'km'

    if travel_type in ('flight', 'air'):
        if origin and destination:
            distance, origin_city, dest_city = calculate_flight_distance(
                origin, destination, db_airports
            )
            if distance:
                quantity = distance
                original_unit = 'km (calculated)'
                normalized_quantity = distance
                normalized_unit = 'passenger-km'
            else:
                flags.append({
                    'rule': 'unknown_airport',
                    'severity': 'warning',
                    'message': f'Cannot calculate distance: unknown airport code {origin} or {destination}',
                })
                quantity = cost  # Fallback to cost-based
                original_unit = currency
                normalized_quantity = cost
                normalized_unit = currency
        else:
            flags.append({
                'rule': 'missing_route',
                'severity': 'warning',
                'message': 'Flight without origin/destination — cannot calculate distance',
            })
            quantity = cost
            original_unit = currency
            normalized_quantity = cost
            normalized_unit = currency

    elif travel_type in ('train', 'rail'):
        # Try route lookup
        origin_lower = origin.lower() if origin else ''
        dest_lower = destination.lower() if destination else ''
        route_key = (origin_lower, dest_lower)

        if route_key in TRAIN_ROUTES:
            quantity = TRAIN_ROUTES[route_key]
            original_unit = 'km (lookup)'
            normalized_quantity = quantity
            normalized_unit = 'passenger-km'
        else:
            # Fallback to cost-based estimation
            quantity = cost
            original_unit = currency
            normalized_quantity = cost
            normalized_unit = currency
            flags.append({
                'rule': 'unknown_route',
                'severity': 'info',
                'message': f'No distance lookup for train route {origin} → {destination}, using cost-based estimate',
            })

    elif travel_type in ('hotel', 'accommodation'):
        quantity = 1  # nights (estimate from cost if needed)
        original_unit = 'night'
        normalized_quantity = 1
        normalized_unit = 'room-night'

    elif travel_type in ('taxi', 'cab'):
        # Estimate ~20 km per taxi trip if no distance given
        quantity = 20
        original_unit = 'km (estimated)'
        normalized_quantity = 20
        normalized_unit = 'km'

    else:
        quantity = cost
        original_unit = currency
        normalized_quantity = cost
        normalized_unit = currency

    # Parse date
    activity_date = parse_date(travel_date)
    if not activity_date:
        flags.append({
            'rule': 'invalid_date',
            'severity': 'warning',
            'message': f'Cannot parse travel date: {travel_date}',
        })

    # Build description
    desc_parts = [classification['activity_type']]
    if origin and destination:
        desc_parts.append(f"{origin} → {destination}")
    elif destination:
        desc_parts.append(f"in {destination}")
    if employee_name:
        desc_parts.append(f"by {employee_name}")
    if purpose:
        desc_parts.append(f"({purpose})")

    record = {
        'organization_id': organization_id,
        'activity_type': classification['activity_type'],
        'scope': 3,
        'category': classification['category'],
        'quantity': quantity,
        'original_unit': original_unit,
        'normalized_quantity': normalized_quantity,
        'normalized_unit': normalized_unit,
        'activity_date': activity_date,
        'description': ' | '.join(desc_parts),
        'suspicious_reasons': flags,
        'suspicious': len(flags) > 0,
        '_emission_activity': travel_type,
        '_fuel_type': travel_type,
    }

    return record
