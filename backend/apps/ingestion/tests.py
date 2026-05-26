from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.activities.models import ActivityRecord, EmissionFactor
from apps.audits.models import AuditLog
from apps.ingestion.models import DataSource, RawRecord
from apps.organizations.models import Organization
from apps.users.models import User
from normalizers.sap_normalizer import normalize_row as normalize_sap_row
from normalizers.travel_normalizer import normalize_row as normalize_travel_row
from normalizers.utility_normalizer import normalize_row as normalize_utility_row


class IngestionPipelineTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme', industry='manufacturing')
        self.user = User.objects.create_user(
            username='analyst',
            password='analyst123',
            organization=self.org,
            role='analyst',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        EmissionFactor.objects.create(
            activity_type='electricity',
            fuel_type='grid_electricity',
            unit='kWh',
            factor_value=0.42,
            source='Test factor',
        )

    def test_utility_upload_creates_raw_activity_and_audit_rows(self):
        csv_file = SimpleUploadedFile(
            'utility.csv',
            (
                b'meter_id,facility,start_date,end_date,usage_kwh,tariff_type\n'
                b'MTR-1,Main Plant,2024-01-01,2024-01-31,100,standard\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post('/api/ingestion/upload/', {
            'file': csv_file,
            'source_type': 'utility',
        }, format='multipart')

        self.assertEqual(response.status_code, 201)
        datasource = DataSource.objects.get()
        self.assertEqual(datasource.status, 'completed')
        self.assertEqual(datasource.processed_rows, 1)
        self.assertEqual(RawRecord.objects.count(), 1)

        activity = ActivityRecord.objects.get()
        self.assertEqual(activity.activity_type, 'Purchased Electricity')
        self.assertEqual(activity.status, 'validated')
        self.assertEqual(activity.normalized_quantity, 100)
        self.assertAlmostEqual(activity.co2e_kg, 42.0)
        self.assertEqual(AuditLog.objects.filter(action='created').count(), 1)


class NormalizerTests(TestCase):
    def test_utility_normalizer_converts_mwh_to_kwh(self):
        normalized = normalize_utility_row({
            'Facility': 'Plant A',
            'Usage (MWh)': '2.5',
            'Start Date': '2024-01-01',
            'End Date': '2024-01-31',
        }, organization_id=1)

        self.assertEqual(normalized['scope'], 2)
        self.assertEqual(normalized['normalized_unit'], 'kWh')
        self.assertEqual(normalized['normalized_quantity'], 2500)

    def test_sap_normalizer_classifies_and_converts_gallons(self):
        normalized = normalize_sap_row({
            'WERKS': '1102',
            'MATNR': 'DSL-FUEL',
            'MENGE': '10',
            'MEINS': 'GAL',
            'BUDAT': '20240131',
        }, organization_id=1)

        self.assertEqual(normalized['scope'], 1)
        self.assertEqual(normalized['category'], 'stationary_combustion')
        self.assertEqual(normalized['normalized_unit'], 'liters')
        self.assertAlmostEqual(normalized['normalized_quantity'], 37.8541)

    def test_travel_normalizer_calculates_known_flight_distance(self):
        normalized = normalize_travel_row({
            'Travel Type': 'flight',
            'Origin': 'DEL',
            'Destination': 'BOM',
            'Date': '2024-01-31',
        }, organization_id=1)

        self.assertEqual(normalized['scope'], 3)
        self.assertEqual(normalized['normalized_unit'], 'passenger-km')
        self.assertGreater(normalized['normalized_quantity'], 1000)
