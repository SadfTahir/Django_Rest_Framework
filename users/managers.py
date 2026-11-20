from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for a user model that logs in with email instead of username."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        # Lowercase the whole address so `John@Mail.com` and `john@mail.com` are one account.
        return super().normalize_email(email).strip().lower()

    def get_by_natural_key(self, email):
        # Used by `authenticate()`: makes login case-insensitive.
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': email})

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        if not email:
            raise ValueError('An email address is required.')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # a None password becomes an unusable password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields['is_superuser'] is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)
