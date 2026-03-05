"""URL routes for the accounts app."""
from django.urls import path

from accounts.views import GoogleLoginView, UserProfileView, TestEmailView

urlpatterns = [
    path("", GoogleLoginView.as_view(), name="google-login"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("test-email/", TestEmailView.as_view(), name="test-email"),
]
