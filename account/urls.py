from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, LogoutView, PasswordResetRequestView, PasswordResetConfirmView, UnifiedLoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', UnifiedLoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetRequestView.as_view(), name='password_reset_confirm'),
]
