"""Abstract base models shared across apps. These never create tables of their own."""

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Adds `created_at` / `updated_at`, maintained automatically by Django."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditedModel(TimeStampedModel):
    """Timestamps plus the users who created and last updated the record.

    Both are set by the API (see `core.views.AuditedModelViewSet`), never by the client.
    `SET_NULL` keeps the record when the user account is deleted.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='%(app_label)s_%(class)s_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='%(app_label)s_%(class)s_updated',
    )

    class Meta:
        abstract = True
