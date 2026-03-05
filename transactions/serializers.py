"""Serializers for the transactions app."""
from rest_framework import serializers

from projects.models import Project
from transactions.models import RecurringTransaction, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "project",
            "transaction_type",
            "amount",
            "category",
            "description",
            "author",
            "stakeholder_author",
            "created_at",
        ]
        read_only_fields = ["id", "author", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return value

    def validate(self, attrs):
        project = attrs.get("project") or (self.instance.project if self.instance else None)
        if project and project.is_locked:
            raise serializers.ValidationError(
                f"Cannot add transactions to a project with status '{project.status}'."
            )
        return attrs


class RecurringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTransaction
        fields = [
            "id",
            "project",
            "transaction_type",
            "amount",
            "category",
            "description",
            "frequency",
            "start_date",
            "end_date",
            "last_generated",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "last_generated", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return value
