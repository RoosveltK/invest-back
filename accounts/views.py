"""
Views for the accounts app.

- GoogleLoginView: Social login via Google OAuth2 token.
- UserProfileView: Retrieve and update the authenticated user's profile.
"""
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from accounts.serializers import UserDetailSerializer, UserUpdateSerializer


@extend_schema(tags=["auth"])
class GoogleLoginView(SocialLoginView):
    """
    Authenticate using a Google OAuth2 access token.

    Send the Google access_token obtained from the frontend's Google Sign-In flow.
    Returns JWT access and refresh tokens on success.
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:8000/api/auth/google/callback/"


@extend_schema(tags=["auth"])
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user
