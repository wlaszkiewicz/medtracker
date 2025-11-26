from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)