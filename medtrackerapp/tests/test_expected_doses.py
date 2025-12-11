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
        self.url = lambda days: reverse("medication-expected-doses-view", args=[self.med.id]) + f"?days={days}"

    def test_expected_doses_valid(self):
        """Valid days parameter returns correct expected doses"""
        response = self.client.get(self.url(5))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.med.id)
        self.assertEqual(response.data["days"], 5)
        self.assertEqual(response.data["expected_doses"], 10)

    def test_missing_days_param(self):
        """Missing days parameter returns 400"""
        url = reverse("medication-expected-doses-view", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_days_param(self):
        """Non-integer or negative days parameter returns 400"""
        response = self.client.get(self.url(-3))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(self.url("abc"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_value_error_from_model(self):
        """If model raises ValueError, API returns 400"""
        self.med.prescribed_per_day = 0
        self.med.save()
        response = self.client.get(self.url(5))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
