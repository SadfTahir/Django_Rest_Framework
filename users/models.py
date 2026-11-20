from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TimeStampedModel

from .managers import UserManager


class User(TimeStampedModel, AbstractUser):
    """Custom user that signs in with a unique, case-insensitive email address."""

    username = None
    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={'unique': 'A user with this email already exists.'},
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # prompted by `createsuperuser` besides email and password

    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Normalise on every save path (API, admin, shell) so uniqueness stays case-insensitive.
        self.email = self.__class__.objects.normalize_email(self.email)
        super().save(*args, **kwargs)
