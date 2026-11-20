from django.contrib.auth.models import update_last_login
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .serializers import LoginSerializer, SignupSerializer, UserSerializer
from .services import build_auth_response


class PublicAuthView(generics.GenericAPIView):
    """Base for endpoints used *before* the client has a valid token.

    Authentication is disabled so a stale/expired token sent by the client
    cannot block signup or login with a 401. Requests are rate-limited
    (scope `auth`) to slow down brute-force attempts.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def get_authenticate_header(self, request):
        # With no authentication classes DRF would turn AuthenticationFailed into a 403.
        # Advertising the Bearer scheme keeps failed logins a proper 401.
        return JWTAuthentication().authenticate_header(request)


class SignupView(PublicAuthView):
    """POST api/v1/user/signup/ — create an account and return JWT tokens."""

    serializer_class = SignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class LoginView(PublicAuthView):
    """POST api/v1/user/login/ — exchange email + password for JWT tokens."""

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        update_last_login(None, user)
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class TokenRefreshView(BaseTokenRefreshView):
    """POST api/v1/user/token/refresh/ — get a new access token from a refresh token."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """GET / PATCH api/v1/user/ — the authenticated user's own profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user
