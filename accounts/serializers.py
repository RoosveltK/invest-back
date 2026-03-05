"""Serializers for the accounts app."""
from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer
from rest_framework import serializers

from accounts.models import CustomUser


class RegisterSerializer(BaseRegisterSerializer):
    """
    Extends dj-rest-auth's RegisterSerializer to capture first_name,
    last_name, and phone_number at registration time.
    Username is not used (email-based auth).
    """

    username = None  # Remove username field
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["first_name"] = self.validated_data.get("first_name", "")
        data["last_name"] = self.validated_data.get("last_name", "")
        data["phone_number"] = self.validated_data.get("phone_number", "")
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer returned on /auth/user/ endpoint."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "is_email_verified",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "is_email_verified", "date_joined"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Allows users to update their own profile (except email)."""

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone_number"]
