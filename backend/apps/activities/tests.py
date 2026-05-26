from django.test import TestCase
from rest_framework.test import APIClient

from apps.activities.models import ActivityRecord
from apps.audits.models import AuditLog
from apps.ingestion.models import DataSource
from apps.organizations.models import Organization
from apps.users.models import User


class ActivityWorkflowTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme', industry='manufacturing')
        self.user = User.objects.create_user(
            username='reviewer',
            password='reviewer123',
            organization=self.org,
            role='analyst',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def create_activity(self, **overrides):
        defaults = {
            'organization': self.org,
            'activity_type': 'Purchased Electricity',
            'scope': 2,
            'category': 'purchased_electricity',
            'quantity': 100,
            'original_unit': 'kWh',
            'normalized_quantity': 100,
            'normalized_unit': 'kWh',
            'co2e_kg': 42,
            'status': 'validated',
        }
        defaults.update(overrides)
        return ActivityRecord.objects.create(**defaults)

    def test_approve_lock_and_locked_edit_protection_work(self):
        activity = self.create_activity(status='flagged', suspicious=True)

        approve_response = self.client.post(
            f'/api/activities/{activity.id}/approve/',
            {'comment': 'Looks correct'},
            format='json',
        )
        self.assertEqual(approve_response.status_code, 200)
        activity.refresh_from_db()
        self.assertEqual(activity.status, 'approved')
        self.assertFalse(activity.suspicious)

        lock_response = self.client.post(f'/api/activities/{activity.id}/lock/')
        self.assertEqual(lock_response.status_code, 200)
        activity.refresh_from_db()
        self.assertTrue(activity.locked)
        self.assertEqual(activity.status, 'locked')

        edit_response = self.client.patch(
            f'/api/activities/{activity.id}/',
            {'normalized_quantity': 120},
            format='json',
        )
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(AuditLog.objects.filter(record=activity).count(), 2)

    def test_bulk_actions_update_records_and_audit_logs(self):
        first = self.create_activity(status='validated')
        second = self.create_activity(status='flagged')

        approve_response = self.client.post('/api/activities/bulk_approve/', {
            'record_ids': [first.id, second.id],
            'comment': 'Batch checked',
        }, format='json')
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.data['approved'], 2)

        lock_response = self.client.post('/api/activities/bulk_lock/', {
            'record_ids': [first.id, second.id],
        }, format='json')
        self.assertEqual(lock_response.status_code, 200)
        self.assertEqual(lock_response.data['locked'], 2)
        self.assertEqual(ActivityRecord.objects.filter(status='locked').count(), 2)
        self.assertEqual(AuditLog.objects.filter(action='approved').count(), 2)
        self.assertEqual(AuditLog.objects.filter(action='locked').count(), 2)

    def test_dashboard_stats_are_aggregated(self):
        self.create_activity(status='validated', scope=1, co2e_kg=10)
        self.create_activity(status='flagged', scope=2, co2e_kg=20)
        self.create_activity(status='approved', scope=3, co2e_kg=30)
        DataSource.objects.create(
            organization=self.org,
            source_type='utility',
            file_name='utility.csv',
            uploaded_by=self.user,
            status='completed',
        )

        response = self.client.get('/api/activities/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_records'], 3)
        self.assertEqual(response.data['pending_review'], 1)
        self.assertEqual(response.data['flagged'], 1)
        self.assertEqual(response.data['approved'], 1)
        self.assertEqual(response.data['total_co2e_kg'], 60)
        self.assertEqual(response.data['scope_1_co2e'], 10)
        self.assertEqual(response.data['scope_2_co2e'], 20)
        self.assertEqual(response.data['scope_3_co2e'], 30)
        self.assertEqual(response.data['recent_uploads'], 1)
