"""Project-wide DRF exception handler.

DRF already turns its own exceptions (validation, auth, 404, throttling…) into
JSON responses. This handler also converts errors that would otherwise surface
as an HTML 500 page into clean JSON responses with a proper status code.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, 'error_dict') else {'detail': exc.messages}
        return Response(detail, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (ProtectedError, RestrictedError)):
        return Response(
            {'detail': 'This record cannot be deleted because other records depend on it.'},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, IntegrityError):
        # e.g. two concurrent sign-ups with the same email both passing validation.
        logger.warning('Integrity error in %s: %s', context.get('view').__class__.__name__, exc)
        return Response(
            {'detail': 'This request conflicts with existing data. Please check unique fields and try again.'},
            status=status.HTTP_409_CONFLICT,
        )

    return None  # anything else is a real bug: let Django return a 500 and log it
