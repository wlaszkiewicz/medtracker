from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication

class MedicationExpectedDosesTests(APITestCase):
    """Tests for GET /api/medications/<id>/expected-doses/?days=X"""

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.url = lambda med_id, days: reverse(
            "medication-expected-doses", args=[med_id]
        ) + f"?days={days}"

    def test_expected_doses_valid(self):
        """Valid request returns 200 with correct expected_doses."""
        response = self.client.get(self.url(self.med.id, 3))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.med.id)
        self.assertEqual(response.data["days"], 3)
        self.assertEqual(response.data["expected_doses"], 6)

    def test_expected_doses_missing_days(self):
        """Missing days query parameter returns 400."""
        url = reverse("medication-expected-doses", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_days(self):
        """Invalid days (negative or non-integer) returns 400."""
        for invalid in [-1, 0, "abc"]:
            response = self.client.get(self.url(self.med.id, invalid))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_nonexistent_medication(self):
        """Requesting a non-existing medication returns 404."""
        response = self.client.get(self.url(999, 3))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
