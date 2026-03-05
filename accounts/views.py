"""
Views for the accounts app.

- GoogleLoginView: Social login via Google OAuth2 token.
- UserProfileView: Retrieve and update the authenticated user's profile.
- TestEmailView: Send a test email for debugging SMTP.
"""
import traceback
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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


@extend_schema(tags=["debug"])
class TestEmailView(APIView):
    """
    Send a test email to the provided address to verify SMTP configuration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        subject = "Coinvest SMTP Test"
        message = "This is a test email from the Coinvest backend."
        
        try:
            sent = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({
                "success": True,
                "sent": sent,
                "message": f"Test email sent to {email}",
                "from_email": settings.DEFAULT_FROM_EMAIL,
                "host": settings.EMAIL_HOST,
                "port": settings.EMAIL_PORT,
                "user": settings.EMAIL_HOST_USER
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "settings": {
                    "EMAIL_HOST": settings.EMAIL_HOST,
                    "EMAIL_PORT": settings.EMAIL_PORT,
                    "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
                    "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
                    "EMAIL_USE_TLS": settings.EMAIL_USE_TLS,
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
