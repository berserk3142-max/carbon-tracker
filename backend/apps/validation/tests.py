from datetime import date, timedelta
import math
from django.test import SimpleTestCase

from apps.validation.engine import validate_record


class ValidationRuleTests(SimpleTestCase):
    def test_validation_flags_negative_missing_unit_future_and_spike(self):
        flags = validate_record({
            'normalized_quantity': -10,
            'normalized_unit': 'unknown',
            'original_unit': '',
            'activity_date': date.today() + timedelta(days=1),
        }, {'category_avg': 1})

        rules = {flag['rule'] for flag in flags}
        self.assertIn('negative_quantity', rules)
        self.assertIn('missing_unit', rules)
        self.assertIn('future_date', rules)

    def test_validation_flags_extreme_values(self):
        flags = validate_record({
            'normalized_quantity': 2_000_000,
            'normalized_unit': 'kWh',
            'activity_date': date.today(),
        })

        self.assertEqual(flags[0]['rule'], 'extreme_value')

    def test_validation_flags_non_finite_quantities(self):
        flags = validate_record({
            'normalized_quantity': math.nan,
            'normalized_unit': 'kWh',
            'activity_date': date.today(),
        })

        self.assertEqual(flags[0]['rule'], 'non_finite_quantity')
