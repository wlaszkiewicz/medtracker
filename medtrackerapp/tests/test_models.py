from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import date, timedelta


class MedicationModelTests(TestCase):
    """Tests for Medication model covering positive and negative paths."""

    def test_str_returns_name_and_dosage(self):
        """__str__ returns formatted string with name and dosage. """

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        """adherence_rate returns 100.0 when all doses are taken."""

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    # expected_doses()

    def test_expected_doses_positive(self):
        """expected_doses returns correct multiplication for normal input."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=3)
        self.assertEqual(med.expected_doses(5), 15)

    def test_expected_doses_zero_days(self):
        """Zero days should return 0 expected doses."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=3)
        self.assertEqual(med.expected_doses(0), 0)

    def test_expected_doses_negative_days_raises(self):
        """Negative day input must raise ValueError."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=3)
        with self.assertRaises(ValueError):
            med.expected_doses(-1)

    def test_expected_doses_invalid_schedule_raises(self):
        """prescribed_per_day <= 0 must raise ValueError."""
        med = Medication.objects.create(name="Ibuprofen", dosage_mg=200, prescribed_per_day=0)
        with self.assertRaises(ValueError):
            med.expected_doses(3)

    # adherence_rate_over_period()

    def test_adherence_rate_over_period_valid(self):
        """Correctly calculates adherence rate in a date range."""
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        today = date.today()
        times = [
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day, 8)),
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day - 1, 8)),
            timezone.make_aware(timezone.datetime(today.year, today.month, today.day - 2, 8)),
        ]

        DoseLog.objects.create(medication=med, taken_at=times[0], was_taken=True)
        DoseLog.objects.create(medication=med, taken_at=times[1], was_taken=False)
        DoseLog.objects.create(medication=med, taken_at=times[2], was_taken=True)

        rate = med.adherence_rate_over_period(today - timedelta(days=2), today)
        self.assertEqual(rate, 66.67)

    def test_adherence_rate_over_period_invalid_dates(self):
        """Start date greater than end date should raise ValueError."""
        med = Medication.objects.create(name="Paracetamol", dosage_mg=500, prescribed_per_day=1)

        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(date(2024, 5, 10), date(2024, 5, 1))

    def test_adherence_rate_over_period_zero_expected_raises(self):
        """prescribed_per_day = 0 should raise ValueError."""
        med = Medication.objects.create(name="Paracetamol", dosage_mg=500, prescribed_per_day=0)

        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(date(2024, 5, 1), date(2024, 5, 1))


class DoseLogModelTests(TestCase):
    """Tests for DoseLog including positive and negative paths."""

    def test_str_representation(self):
        """__str__ returns formatted string with medication name and status."""
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        taken_at = timezone.now()
        log = DoseLog.objects.create(medication=med, taken_at=taken_at, was_taken=True)

        self.assertIn("Aspirin", str(log))
        self.assertIn("Taken", str(log))

    def test_ordering_descending(self):
        """Meta.ordering ensures newest logs come first."""
        med = Medication.objects.create(name="Vitamin D", dosage_mg=1000, prescribed_per_day=1)

        t1 = timezone.now() - timedelta(hours=5)
        t2 = timezone.now()

        log_old = DoseLog.objects.create(medication=med, taken_at=t1)
        log_new = DoseLog.objects.create(medication=med, taken_at=t2)

        logs = list(DoseLog.objects.all())
        self.assertEqual(logs[0], log_new)
        self.assertEqual(logs[1], log_old)

    def test_doselog_missing_medication_raises(self):
        """DoseLog must have a medication FK."""
        taken_at = timezone.now()
        with self.assertRaises(Exception):  # IntegrityError depending on DB backend
            DoseLog.objects.create(medication=None, taken_at=taken_at)
