from django.urls import path

from .views import CurrentUserView, LoginView, SignupView, TokenRefreshView

# Mounted at api/v1/user/ (see config/urls.py)
urlpatterns = [
    path('', CurrentUserView.as_view(), name='user-detail'),
    path('signup/', SignupView.as_view(), name='user-signup'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='user-token-refresh'),
]
