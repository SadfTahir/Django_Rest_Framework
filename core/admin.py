from django.contrib import admin


class AuditedModelAdmin(admin.ModelAdmin):
    """Fills `created_by` / `updated_by` for records saved through the admin panel."""

    audit_readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    def get_readonly_fields(self, request, obj=None):
        return [*super().get_readonly_fields(request, obj), *self.audit_readonly_fields]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
