from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication
from medtrackerapp.models import Note


class NoteViewTests(APITestCase):
    """Tests for /api/notes/ endpoint."""

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        self.list_url = reverse("note-list")

    def test_create_note(self):
        """Creating a note with valid data succeeds."""
        data = {"medication": self.med.id, "text": "Take at night"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Take at night")

    def test_list_notes(self):
        """Listing notes returns all existing notes."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_note(self):
        """Retrieving a specific note by ID works correctly."""
        note = Note.objects.create(medication=self.med, text="Retrieve me")
        url = reverse("note-detail", args=[note.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Retrieve me")

    def test_delete_note(self):
        """Deleting a note removes it from the database."""
        note = Note.objects.create(medication=self.med, text="Delete me")
        url = reverse("note-detail", args=[note.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 0)

    def test_update_not_allowed(self):
        """Updating a note is not allowed and returns 405."""
        note = Note.objects.create(medication=self.med, text="Don't update me")
        url = reverse("note-detail", args=[note.id])
        response = self.client.put(url, {"text": "Update attempt"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
