from rest_framework import viewsets

# GET, POST, PATCH, DELETE only (PUT is intentionally excluded).
CRUD_METHODS = ['get', 'post', 'patch', 'delete', 'head', 'options']


class AuditedModelViewSet(viewsets.ModelViewSet):
    """ModelViewSet that records which user created / last updated each record.

    Use with models inheriting `core.models.AuditedModel`.
    """

    http_method_names = CRUD_METHODS

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
