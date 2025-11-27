from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from medtrackerapp.models import Medication, DoseLog


class MedicationViewTests(APITestCase):
    """Tests for Medication CRUD API endpoints."""

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.list_url = reverse("medication-list")


    def test_list_medications_valid_data(self):
        """List endpoint returns existing medications."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")

    def test_create_medication_valid(self):
        """Create a medication with valid data."""
        data = {
            "name": "Ibuprofen",
            "dosage_mg": 200,
            "prescribed_per_day": 3
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 2)

    def test_create_medication_invalid(self):
        """Creating with missing required fields should fail."""
        data = {"name": ""}  # invalid
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_medication(self):
        """Retrieve a specific medication."""
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_retrieve_invalid_medication(self):
        """Retrieving non-existing medication returns 404."""
        url = reverse("medication-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_medication(self):
        """Update a medication with valid data."""
        url = reverse("medication-detail", args=[self.med.id])
        data = {"name": "Updated", "dosage_mg": 150, "prescribed_per_day": 1}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated")

    def test_delete_medication(self):
        """Deleting a medication removes it."""
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Medication.objects.count(), 0)


class DoseLogViewTests(APITestCase):
    """Tests for DoseLog CRUD and filter endpoints."""

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        now = timezone.now()

        self.log1 = DoseLog.objects.create(
            medication=self.med,
            taken_at=now - timedelta(days=2),
            was_taken=True
        )
        self.log2 = DoseLog.objects.create(
            medication=self.med,
            taken_at=now - timedelta(days=1),
            was_taken=False
        )

        self.list_url = reverse("doselog-list")

    def test_list_logs(self):
        """List endpoint returns dose logs."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_log_valid(self):
        """Create a dose log with valid data."""
        data = {
            "medication": self.med.id,
            "taken_at": (timezone.now()).isoformat(),
            "was_taken": True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_log_invalid(self):
        """Creating with invalid data should fail."""
        data = {
            "medication": "",
            "taken_at": "",
            "was_taken": True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_log(self):
        """Retrieve a specific dose log."""
        url = reverse("doselog-detail", args=[self.log1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.log1.id)

    def test_retrieve_invalid_log(self):
        """Retrieving non-existing log returns 404."""
        url = reverse("doselog-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_log(self):
        """Deleting a dose log removes it."""
        url = reverse("doselog-detail", args=[self.log1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoseLog.objects.count(), 1)

    def test_filter_logs_valid_range(self):
        """Filtering logs by valid start/end dates returns correct results."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {
            "start": (timezone.now() - timedelta(days=3)).date().isoformat(),
            "end": timezone.now().date().isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_logs_missing_params(self):
        """Filter endpoint returns 400 if end date is missing or invalid."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "2020-01-01", "end": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_logs_invalid_dates(self):
        """Filter endpoint returns 400 for invalid date format."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "nope", "end": "also_nope"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
