from rest_framework import serializers

from users.serializers import UserSummarySerializer

from .models import Make, Vehicle

AUDIT_FIELDS = ['created_by', 'updated_by', 'created_at', 'updated_at']


class AuditedModelSerializer(serializers.ModelSerializer):
    """Exposes who created / last updated a record. Always read-only: set by the view."""

    created_by = UserSummarySerializer(read_only=True)
    updated_by = UserSummarySerializer(read_only=True)


class MakeSerializer(AuditedModelSerializer):
    class Meta:
        model = Make
        fields = ['id', 'name', 'founded_at', 'logo', *AUDIT_FIELDS]
        read_only_fields = ['id', *AUDIT_FIELDS]


class VehicleSerializer(AuditedModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'make_name', 'name', 'model', 'color', 'engine', 'image',
            *AUDIT_FIELDS,
        ]
        read_only_fields = ['id', *AUDIT_FIELDS]
