"""
Ingestion Service — The core data pipeline.

Handles the full flow:
  Upload CSV → Parse Raw Data → Store Raw Records →
  Normalize → Validate → Flag → Create ActivityRecords

Each source type (SAP, utility, travel) has its own normalizer
but follows the same pipeline pattern.
"""
import io
import logging
import pandas as pd
from django.db import transaction

from apps.ingestion.models import DataSource, RawRecord
from apps.activities.models import ActivityRecord, EmissionFactor
from apps.audits.models import AuditLog
from apps.validation.engine import validate_record, get_category_averages
from normalizers import sap_normalizer, utility_normalizer, travel_normalizer

logger = logging.getLogger(__name__)

# Map source types to their normalizer modules
NORMALIZERS = {
    'sap': sap_normalizer,
    'utility': utility_normalizer,
    'travel': travel_normalizer,
}


def process_upload(datasource: DataSource, file_content: bytes) -> dict:
    """
    Main ingestion pipeline. Processes a CSV upload end-to-end.

    Steps:
    1. Parse CSV into rows
    2. Store each row as an immutable RawRecord
    3. Normalize each row using the appropriate normalizer
    4. Run validation rules
    5. Look up emission factors and calculate CO2e
    6. Create ActivityRecords

    Returns a summary dict with counts.
    """
    datasource.status = 'parsing'
    datasource.save(update_fields=['status'])

    results = {
        'total_rows': 0,
        'processed': 0,
        'failed': 0,
        'flagged': 0,
        'errors': [],
    }

    try:
        # Step 1: Parse CSV
        df = pd.read_csv(io.BytesIO(file_content))
        df = df.where(pd.notnull(df), None)  # Replace NaN with None
        results['total_rows'] = len(df)
        datasource.total_rows = len(df)
        datasource.save(update_fields=['total_rows'])

        if len(df) == 0:
            datasource.status = 'failed'
            datasource.error_summary = 'Empty CSV file'
            datasource.save(update_fields=['status', 'error_summary'])
            results['errors'].append('Empty CSV file')
            return results

        # Get the normalizer for this source type
        normalizer = NORMALIZERS.get(datasource.source_type)
        if not normalizer:
            datasource.status = 'failed'
            datasource.error_summary = f'Unknown source type: {datasource.source_type}'
            datasource.save(update_fields=['status', 'error_summary'])
            return results

        with transaction.atomic():
            datasource.status = 'normalizing'
            datasource.save(update_fields=['status'])

            # Get category averages for spike detection
            org_id = datasource.organization_id
            category_avgs = get_category_averages(org_id)

            # Load airport data from DB for travel normalizer
            db_airports = {}
            if datasource.source_type == 'travel':
                from apps.organizations.models import AirportLookup
                for airport in AirportLookup.objects.values('iata_code', 'latitude', 'longitude', 'city'):
                    db_airports[airport['iata_code']] = {
                        'lat': airport['latitude'],
                        'lon': airport['longitude'],
                        'city': airport['city'],
                    }

            emission_factors = {}
            for factor in EmissionFactor.objects.all().order_by('id'):
                emission_factors[(factor.activity_type, factor.fuel_type)] = factor
                emission_factors.setdefault((factor.activity_type, ''), factor)

            # Step 2-6: Process each row
            raw_records_to_create = []
            activity_records_to_create = []
            raw_records_to_update = []

            for idx, row in enumerate(df.to_dict(orient='records'), start=1):
                raw_payload = {k: ('' if pd.isna(v) else str(v)) for k, v in row.items()}
                raw_records_to_create.append(
                    RawRecord(
                        datasource=datasource,
                        row_number=idx,
                        raw_payload=raw_payload,
                        ingestion_status='pending',
                    )
                )

            raw_records = RawRecord.objects.bulk_create(raw_records_to_create)
            if any(record.pk is None for record in raw_records):
                raw_records = list(
                    RawRecord.objects.filter(datasource=datasource).order_by('row_number')
                )

            for raw_record in raw_records:
                try:
                    # Step 3: Normalize
                    if datasource.source_type == 'travel':
                        normalized = normalizer.normalize_row(
                            raw_record.raw_payload, org_id, db_airports
                        )
                    else:
                        normalized = normalizer.normalize_row(
                            raw_record.raw_payload, org_id
                        )

                    # Step 4: Run validation
                    context = {}
                    activity_type = normalized.get('activity_type', '')
                    norm_unit = normalized.get('normalized_unit', '')
                    avg_key = f"{activity_type}_{norm_unit}"
                    if avg_key in category_avgs:
                        context['category_avg'] = category_avgs[avg_key]

                    validation_flags = validate_record(normalized, context)

                    # Merge normalizer flags + validation flags
                    all_flags = normalized.get('suspicious_reasons', []) + validation_flags
                    is_suspicious = len(all_flags) > 0
                    has_errors = any(f.get('severity') == 'error' for f in all_flags)

                    # Step 5: Look up emission factor and calculate CO2e
                    emission_factor_obj = None
                    emission_factor_value = None
                    co2e_kg = None

                    emission_activity = normalized.pop('_emission_activity', '')
                    fuel_type = normalized.pop('_fuel_type', '')
                    ef = (
                        emission_factors.get((emission_activity, fuel_type))
                        or emission_factors.get((emission_activity, ''))
                    )
                    if ef:
                        emission_factor_obj = ef
                        emission_factor_value = ef.factor_value
                        norm_qty = normalized.get('normalized_quantity', 0)
                        if isinstance(norm_qty, (int, float)) and not pd.isna(norm_qty):
                            co2e_kg = norm_qty * ef.factor_value

                    # Step 6: Determine status
                    status = 'flagged' if has_errors or is_suspicious else 'validated'

                    activity_records_to_create.append(
                        ActivityRecord(
                            organization_id=org_id,
                            raw_record=raw_record,
                            datasource=datasource,
                            activity_type=normalized['activity_type'],
                            scope=normalized['scope'],
                            category=normalized['category'],
                            quantity=normalized['quantity'],
                            original_unit=normalized['original_unit'],
                            normalized_quantity=normalized['normalized_quantity'],
                            normalized_unit=normalized['normalized_unit'],
                            emission_factor=emission_factor_obj,
                            emission_factor_value=emission_factor_value,
                            co2e_kg=co2e_kg,
                            activity_date=normalized.get('activity_date'),
                            description=normalized.get('description', ''),
                            plant_code=normalized.get('plant_code', ''),
                            facility=normalized.get('facility', ''),
                            status=status,
                            suspicious=is_suspicious,
                            suspicious_reasons=all_flags,
                        )
                    )

                    raw_record.ingestion_status = 'normalized'
                    raw_record.error_message = ''
                    raw_records_to_update.append(raw_record)

                    results['processed'] += 1
                    if is_suspicious:
                        results['flagged'] += 1

                except Exception as e:
                    logger.error(f"Error processing row {raw_record.row_number}: {e}")
                    raw_record.ingestion_status = 'failed'
                    raw_record.error_message = str(e)
                    raw_records_to_update.append(raw_record)
                    results['failed'] += 1
                    results['errors'].append(f"Row {raw_record.row_number}: {str(e)}")

            if raw_records_to_update:
                RawRecord.objects.bulk_update(
                    raw_records_to_update,
                    ['ingestion_status', 'error_message'],
                )

            if activity_records_to_create:
                activities = ActivityRecord.objects.bulk_create(activity_records_to_create)
                if any(activity.pk is None for activity in activities):
                    activities = list(ActivityRecord.objects.filter(datasource=datasource))
                AuditLog.objects.bulk_create([
                    AuditLog(
                        record=activity,
                        action='created',
                        changed_by=datasource.uploaded_by,
                        new_values={
                            'status': activity.status,
                            'co2e_kg': activity.co2e_kg,
                        },
                    )
                    for activity in activities
                ])

        # Update datasource status
        datasource.processed_rows = results['processed']
        datasource.failed_rows = results['failed']
        if results['failed'] > 0 and results['processed'] > 0:
            datasource.status = 'partial'
        elif results['failed'] > 0:
            datasource.status = 'failed'
        else:
            datasource.status = 'completed'

        if results['errors']:
            datasource.error_summary = '; '.join(results['errors'][:10])

        datasource.save()

    except Exception as e:
        logger.error(f"Pipeline error for datasource {datasource.id}: {e}")
        datasource.status = 'failed'
        datasource.error_summary = str(e)
        datasource.save(update_fields=['status', 'error_summary'])
        results['errors'].append(str(e))

    return results
