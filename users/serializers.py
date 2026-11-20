from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

PASSWORD_FIELD_KWARGS = {
    'write_only': True,
    'trim_whitespace': False,  # spaces are valid password characters
    'max_length': 128,
    'style': {'input_type': 'password'},
}


class UniqueEmailMixin:
    """Case-insensitive email uniqueness check (replaces DRF's exact-match UniqueValidator)."""

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        queryset = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email


class UserSummarySerializer(serializers.ModelSerializer):
    """Compact, read-only user representation, e.g. for `created_by` / `updated_by`."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        read_only_fields = fields


class UserSerializer(UniqueEmailMixin, serializers.ModelSerializer):
    """The authenticated user's own profile (GET / PATCH)."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'date_joined', 'last_login', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
        extra_kwargs = {'email': {'validators': []}}  # handled by UniqueEmailMixin


class SignupSerializer(UniqueEmailMixin, serializers.ModelSerializer):
    password = serializers.CharField(**PASSWORD_FIELD_KWARGS)
    password_confirm = serializers.CharField(**PASSWORD_FIELD_KWARGS)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {'email': {'validators': []}}

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        # Run AUTH_PASSWORD_VALIDATORS (length, common, numeric, similarity to email/name).
        candidate = User(
            email=attrs['email'],
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            password_validation.validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(**PASSWORD_FIELD_KWARGS)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            email=User.objects.normalize_email(attrs['email']),
            password=attrs['password'],
        )
        # One generic message for wrong email, wrong password or inactive account,
        # so the response never reveals which emails are registered.
        if user is None:
            raise AuthenticationFailed('Invalid email or password.')
        attrs['user'] = user
        return attrs
