"""Serializers for the projects app."""
from rest_framework import serializers

from projects.models import Project, Stakeholder


class StakeholderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Stakeholder
        fields = [
            "id",
            "user",
            "project",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone_number",
            "job_title",
            "role",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    remaining_budget = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    total_expenses = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    total_income = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    stakeholder_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "project_type",
            "start_date",
            "end_date",
            "tag",
            "initial_budget",
            "remaining_budget",
            "total_expenses",
            "total_income",
            "description",
            "documents",
            "photos",
            "status",
            "owner",
            "stakeholder_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "remaining_budget",
            "total_expenses",
            "total_income",
            "stakeholder_count",
            "created_at",
            "updated_at",
        ]

    def get_stakeholder_count(self, obj):
        return obj.stakeholders.count()

    def validate_status(self, value):
        """
        Prevent manually setting status via the generic update endpoint
        (status changes go through dedicated actions: close, pause, abandon).
        """
        instance = getattr(self, "instance", None)
        if instance and instance.status != value:
            raise serializers.ValidationError(
                "Use the dedicated action endpoints to change project status."
            )
        return value


class ProjectStatusSerializer(serializers.Serializer):
    """Used by owner-only status-change actions (close, pause, abandon, reopen)."""

    status = serializers.ChoiceField(choices=Project.Status.choices)
