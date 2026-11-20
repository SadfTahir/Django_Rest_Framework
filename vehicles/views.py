from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from core.views import AuditedModelViewSet

from .filters import MakeFilter, VehicleFilter
from .models import Make, Vehicle
from .serializers import MakeSerializer, VehicleSerializer

# Authentication is required by the global DEFAULT_PERMISSION_CLASSES (IsAuthenticated).

UPLOAD_PARSERS = [MultiPartParser, FormParser, JSONParser]  # multipart for image uploads


class MakeViewSet(AuditedModelViewSet):
    queryset = Make.objects.select_related('created_by', 'updated_by')
    serializer_class = MakeSerializer
    filterset_class = MakeFilter
    parser_classes = UPLOAD_PARSERS
    search_fields = ['name']
    ordering_fields = ['name', 'founded_at', 'created_at', 'updated_at']


class VehicleViewSet(AuditedModelViewSet):
    queryset = Vehicle.objects.select_related('make', 'created_by', 'updated_by')
    serializer_class = VehicleSerializer
    filterset_class = VehicleFilter
    parser_classes = UPLOAD_PARSERS
    search_fields = ['name', 'model', 'color', 'make__name']
    ordering_fields = ['name', 'model', 'engine', 'created_at', 'updated_at']
