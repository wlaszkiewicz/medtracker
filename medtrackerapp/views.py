from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .models import Medication, DoseLog
from .serializers import MedicationSerializer, DoseLogSerializer
from .models import Note
from .serializers import NoteSerializer
from rest_framework.filters import SearchFilter


class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.

    Provides standard CRUD operations via the Django REST Framework
    `ModelViewSet`, as well as a custom action for retrieving
    additional information from an external API (OpenFDA).

    Endpoints:
        - GET /medications/ — list all medications
        - POST /medications/ — create a new medication
        - GET /medications/{id}/ — retrieve a specific medication
        - PUT/PATCH /medications/{id}/ — update a medication
        - DELETE /medications/{id}/ — delete a medication
        - GET /medications/{id}/info/ — fetch external drug info from OpenFDA
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """
        Retrieve external drug information from the OpenFDA API.

        Calls the `Medication.fetch_external_info()` method, which
        delegates to the `DrugInfoService` for API access.

        Args:
            request (Request): The current HTTP request.
            pk (int): Primary key of the medication record.

        Returns:
            Response:
                - 200 OK: External API data returned successfully.
                - 502 BAD GATEWAY: If the external API request failed.

        Example:
            GET /medications/1/info/
        """
        medication = self.get_object()
        data = medication.fetch_external_info()

        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)


    @action(detail=True, methods=["get"], url_path="expected-doses")
    def expected_doses_view(self, request, pk=None):
        """
        Retrieve the expected doses of a medication over a specified number of days.

        This method is a custom action for the `MedicationViewSet` that calculates
        the expected doses of a medication based on the `days` query parameter.

        Args:
            request (Request): The current HTTP request, which should include the
                `days` query parameter specifying the number of days.
            pk (int): The primary key of the medication record.

        Returns:
            Response:
                - 200 OK: A JSON object containing the medication ID, the number of days,
                  and the calculated expected doses.
                - 400 BAD REQUEST: If the `days` parameter is missing, invalid, or if
                  the calculation raises a `ValueError`.

        """
        medication = self.get_object()

        days_param = request.query_params.get("days")

        try:
            if days_param is None:
                raise ValueError("Missing 'days' parameter")
            days = int(days_param)
            if days <= 0:
                raise ValueError("'days' must be positive")
        except (ValueError, TypeError):
            return Response({"error": "Invalid 'days' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doses = medication.expected_doses(days)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "medication_id": medication.id,
            "days": days,
            "expected_doses": doses
        }, status=status.HTTP_200_OK)

class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.

    A DoseLog represents an event where a medication dose was either
    taken or missed. This viewset provides standard CRUD operations
    and a custom filtering action by date range.

    Endpoints:
        - GET /logs/ — list all dose logs
        - POST /logs/ — create a new dose log
        - GET /logs/{id}/ — retrieve a specific log
        - PUT/PATCH /logs/{id}/ — update a dose log
        - DELETE /logs/{id}/ — delete a dose log
        - GET /logs/filter/?start=YYYY-MM-DD&end=YYYY-MM-DD —
          filter logs within a date range
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """
        Retrieve all dose logs within a given date range.

        Query Parameters:
            - start (YYYY-MM-DD): Start date of the range (inclusive).
            - end (YYYY-MM-DD): End date of the range (inclusive).

        Returns:
            Response:
                - 200 OK: A list of dose logs between the two dates.
                - 400 BAD REQUEST: If start or end parameters are missing or invalid.

        Example:
            GET /logs/filter/?start=2025-11-01&end=2025-11-07
        """
        start = parse_date(request.query_params.get("start"))
        end = parse_date(request.query_params.get("end"))

        if not start or not end:
            return Response(
                {"error": "Both 'start' and 'end' query parameters are required and must be valid dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            taken_at__date__gte=start,
            taken_at__date__lte=end
        ).order_by("taken_at")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notes.

    This viewset provides standard CRUD operations for the `Note` model.
    It allows creating, retrieving, listing, and deleting notes, while
    restricting unsupported HTTP methods like PUT and PATCH.

    Attributes:
        queryset (QuerySet): The set of `Note` objects to be managed by this viewset.
        serializer_class (Serializer): The serializer class used to convert `Note` objects
            to and from JSON representations.
        http_method_names (list): The list of allowed HTTP methods for this viewset.
    """
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    filter_backends = (SearchFilter,)
    search_fields = ["medication__name"]

    http_method_names = ["get", "post", "delete", "head", "options"]
