from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from medtrackerapp.services import DrugInfoService


class DrugInfoServiceTests(APITestCase):
    """Tests for external API integration via DrugInfoService, using mocks."""

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_success(self, mock_get):
        """Mock a successful API response and verify parsed output."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "openfda": {
                    "generic_name": ["ibuprofen"],
                    "manufacturer_name": ["Bayer"]
                },
                "warnings": ["Do not exceed 6 pills per day"],
                "purpose": ["Pain relief"]
            }]
        }
        mock_get.return_value = mock_response

        data = DrugInfoService.get_drug_info("ibuprofen")

        self.assertEqual(data["name"], "ibuprofen")
        self.assertEqual(data["manufacturer"], "Bayer")
        self.assertIn("Pain relief", data["purpose"])

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_api_error(self, mock_get):
        """Mock non-200 status codes and ensure ValueError is raised."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("ibuprofen")

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_no_results(self, mock_get):
        """Mock an empty results list and ensure ValueError is raised."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("ibuprofen")

    def test_get_drug_info_missing_name_raises(self):
        """Empty drug_name should raise ValueError."""
        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("")