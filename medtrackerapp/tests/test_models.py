from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import date, timedelta
from django.db import IntegrityError
from unittest.mock import patch


class MedicationModelTests(TestCase):
    """Tests for Medication model covering positive and negative paths."""

    def setUp(self):
        """Set up a base medication for generic tests."""
        self.base_med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    def test_str_returns_name_and_dosage(self):
        """__str__ returns formatted string with name and dosage. """
        self.assertEqual(str(self.base_med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        """adherence_rate returns 100.0 when all doses are taken."""
        now = timezone.now()
        DoseLog.objects.create(medication=self.base_med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=self.base_med, taken_at=now - timedelta(hours=1))

        adherence = self.base_med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    # expected_doses()

    def test_expected_doses_positive(self):
        """expected_doses returns correct multiplication for normal input."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=3)
        self.assertEqual(med.expected_doses(5), 15)

    def test_expected_doses_zero_days(self):
        """Zero days should return 0 expected doses."""
        self.assertEqual(self.base_med.expected_doses(0), 0)

    def test_expected_doses_negative_days_raises(self):
        """Negative day input must raise ValueError."""
        with self.assertRaises(ValueError):
            self.base_med.expected_doses(-1)

    def test_expected_doses_invalid_schedule_raises(self):
        """prescribed_per_day <= 0 must raise ValueError."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=0)
        with self.assertRaises(ValueError):
            med.expected_doses(3)

    # adherence_rate_over_period()

    def test_adherence_rate_over_period_valid(self):
        """Correctly calculates adherence rate in a date range."""
        today = date.today()
        times = [
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day, 8)),
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day - 1, 8)),
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day - 2, 8)),
        ]

        DoseLog.objects.create(medication=self.base_med, taken_at=times[0], was_taken=True)
        DoseLog.objects.create(medication=self.base_med, taken_at=times[1], was_taken=False)
        DoseLog.objects.create(medication=self.base_med, taken_at=times[2], was_taken=True)

        rate = self.base_med.adherence_rate_over_period(today - timedelta(days=2), today)
        self.assertEqual(rate, 33.33)

    def test_adherence_rate_over_period_invalid_dates(self):
        """Start date greater than end date should raise ValueError."""
        with self.assertRaises(ValueError):
            self.base_med.adherence_rate_over_period(date(2024, 5, 10), date(2024, 5, 1))


    def test_adherence_rate_over_period_zero_expected(self):
        """If expected_doses() = 0, returns 0.0 instead of dividing."""
        rate = self.base_med.adherence_rate_over_period(date(2024, 5, 1), date(2024, 5, 1))
        self.assertEqual(rate, 0.0)

    def test_adherence_rate_over_period_zero_expected_branch(self):
        """Force expected_doses() to return 0 to cover the branch in adherence_rate_over_period. """

        # expected_doses() can never naturally return 0 because for it to do so
        # days would have to be 0 but days is always > 0 if start_date <= end_date (because we add 1)
        # or prescribed_per_day would have to be 0
        # but either of these would raise ValueError before reaching this branch.
        # so I mocked expected_doses it to return 0 so coverage is 100%.

        with patch.object(Medication, "expected_doses", return_value=0):
            rate = self.base_med.adherence_rate_over_period(date(2024, 5, 1), date(2024, 5, 1))
            self.assertEqual(rate, 0.0)

class MedicationExternalInfoTests(TestCase):
    """Tests for fetch_external_info method with success and failure paths."""
    def setUp(self):
        """Set up a base medication for generic tests."""
        self.base_med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_success(self, mock_get_info):
        """fetch_external_info returns API data if service works."""
        mock_get_info.return_value = {"name": "Aspirin"}

        result = self.base_med.fetch_external_info()

        self.assertEqual(result, {"name": "Aspirin"})
        mock_get_info.assert_called_once_with("Aspirin")

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_failure(self, mock_get_info):
        """fetch_external_info returns {'error': message} on exception."""
        mock_get_info.side_effect = Exception("API dead")

        result = self.base_med.fetch_external_info()

        self.assertEqual(result, {"error": "API dead"})


class DoseLogModelTests(TestCase):
    """Tests for DoseLog including positive and negative paths."""

    def setUp(self):
        """Set up a base medication for generic tests."""
        self.base_med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    def test_str_representation(self):
        """__str__ returns formatted string with medication name and status."""
        taken_at = timezone.now()
        log = DoseLog.objects.create(medication=self.base_med, taken_at=taken_at, was_taken=True)

        self.assertIn("Aspirin", str(log))
        self.assertIn("Taken", str(log))

    def test_ordering_descending(self):
        """Meta.ordering ensures newest logs come first."""

        t1 = timezone.now() - timedelta(hours=5)
        t2 = timezone.now()

        log_old = DoseLog.objects.create(medication=self.base_med, taken_at=t1)
        log_new = DoseLog.objects.create(medication=self.base_med, taken_at=t2)

        logs = list(DoseLog.objects.all())
        self.assertEqual(logs[0], log_new)
        self.assertEqual(logs[1], log_old)

    def test_doselog_missing_medication_raises(self):
        """DoseLog must have a medication FK."""
        taken_at = timezone.now()
        with self.assertRaises(IntegrityError):
            DoseLog.objects.create(medication=None, taken_at=taken_at)
