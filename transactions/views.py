"""
Views for the transactions app.

TransactionViewSet:
  - Scoped to projects the user is a member of.
  - Shareholder sees ONLY their own Income transactions.
  - Locked project guard on create/update.
  - Broadcasts WebSocket event on creation.

RecurringTransactionViewSet:
  - Owner/Collaborator only.
"""
import asyncio

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from projects.models import Project, Stakeholder
from projects.permissions import get_stakeholder_role
from transactions.models import RecurringTransaction, Transaction
from transactions.permissions import RecurringTransactionPermission, TransactionPermission
from transactions.serializers import RecurringTransactionSerializer, TransactionSerializer


def _broadcast_transaction(project_id: int, data: dict):
    try:
        from realtime.consumers import ProjectConsumer
        asyncio.run(ProjectConsumer.broadcast_update(project_id, {"type": "transaction.created", **data}))
    except Exception:
        pass


@extend_schema_view(
    list=extend_schema(summary="List transactions for a project", tags=["transactions"]),
    create=extend_schema(summary="Create a transaction", tags=["transactions"]),
    retrieve=extend_schema(summary="Get transaction details", tags=["transactions"]),
    update=extend_schema(summary="Update a transaction", tags=["transactions"]),
    partial_update=extend_schema(summary="Partially update a transaction", tags=["transactions"]),
    destroy=extend_schema(summary="Delete a transaction", tags=["transactions"]),
)
class TransactionViewSet(viewsets.ModelViewSet):
    """
    CRUD for transactions.
    - Shareholders only see their own income transactions.
    - Locked project blocks create/update/delete.
    """

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, TransactionPermission]

    def get_queryset(self):
        user = self.request.user
        # Get all projects the user belongs to
        user_stakeholders = Stakeholder.objects.filter(user=user).select_related("project")

        allowed_project_ids = []
        shareholder_project_ids = []

        for sh in user_stakeholders:
            allowed_project_ids.append(sh.project_id)
            if sh.role == Stakeholder.Role.SHAREHOLDER:
                shareholder_project_ids.append(sh.project_id)

        qs = Transaction.objects.filter(
            project_id__in=allowed_project_ids
        ).select_related("project", "author")

        # Shareholders: only their own income transactions
        if shareholder_project_ids:
            non_shareholder_qs = qs.exclude(project_id__in=shareholder_project_ids)
            shareholder_qs = qs.filter(
                project_id__in=shareholder_project_ids,
                transaction_type=Transaction.TransactionType.INCOME,
                stakeholder_author__user=user,
            )
            return (non_shareholder_qs | shareholder_qs).distinct()

        return qs

    def perform_create(self, serializer):
        transaction = serializer.save(author=self.request.user)
        _broadcast_transaction(
            transaction.project_id,
            TransactionSerializer(transaction).data,
        )


@extend_schema_view(
    list=extend_schema(summary="List recurring transaction rules for a project", tags=["transactions"]),
    create=extend_schema(summary="Create a recurring transaction rule", tags=["transactions"]),
    retrieve=extend_schema(summary="Get a recurring transaction rule", tags=["transactions"]),
    update=extend_schema(summary="Update a recurring transaction rule", tags=["transactions"]),
    partial_update=extend_schema(summary="Partially update a recurring transaction rule", tags=["transactions"]),
    destroy=extend_schema(summary="Delete a recurring transaction rule", tags=["transactions"]),
)
class RecurringTransactionViewSet(viewsets.ModelViewSet):
    """CRUD for recurring transaction rules. Owner/Collaborator only."""

    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, RecurringTransactionPermission]

    def get_queryset(self):
        user_projects = Project.objects.filter(stakeholders__user=self.request.user)
        return RecurringTransaction.objects.filter(project__in=user_projects).select_related("project")
