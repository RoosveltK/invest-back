"""
Custom allauth adapter for email-only authentication (no username).
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    """Override username-related allauth behaviour."""

    def is_open_for_signup(self, request):
        return True

    def populate_username(self, request, user):
        """Our model has no username field — skip entirely."""
        pass

    def save_user(self, request, user, form, commit=True):
        """Save without setting a username."""
        data = form.cleaned_data
        user.email = data.get("email", "")
        user.first_name = data.get("first_name", "")
        user.last_name = data.get("last_name", "")
        if "password1" in data:
            user.set_password(data["password1"])
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Build the activation URL to point to the frontend application."""
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
        return f"{frontend_url}/verify/{emailconfirmation.key}"


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Link social accounts by email to existing CustomUser accounts."""

    def pre_social_login(self, request, sociallogin):
        """
        If a user with the same email already exists, connect the social
        account to that user instead of creating a new one.
        """
        if sociallogin.is_existing:
            return
        if "email" not in sociallogin.account.extra_data:
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            email = sociallogin.account.extra_data["email"].lower()
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        When creating a completely new user via a social provider (Google),
        automatically mark their email as verified.
        """
        user = super().save_user(request, sociallogin, form)
        # Social logins are implicitly verified by the provider
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return user
