from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer


def issue_tokens(user):
    """Create a JWT refresh/access pair for `user`."""
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def build_auth_response(user):
    """Response body shared by signup and login."""
    return {'user': UserSerializer(user).data, 'tokens': issue_tokens(user)}
