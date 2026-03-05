"""URL routes for the accounts app."""
from django.urls import path

from accounts.views import GoogleLoginView, UserProfileView

urlpatterns = [
    path("", GoogleLoginView.as_view(), name="google-login"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
]
