from django.contrib import admin

from core.admin import AuditedModelAdmin

from .models import Make, Vehicle


@admin.register(Make)
class MakeAdmin(AuditedModelAdmin):
    list_display = ['id', 'name', 'founded_at', 'created_by', 'created_at']
    list_select_related = ['created_by']
    search_fields = ['name']


@admin.register(Vehicle)
class VehicleAdmin(AuditedModelAdmin):
    list_display = ['id', 'make', 'name', 'model', 'color', 'engine', 'created_by', 'created_at']
    list_select_related = ['make', 'created_by']
    list_filter = ['make', 'color']
    search_fields = ['name', 'model']
