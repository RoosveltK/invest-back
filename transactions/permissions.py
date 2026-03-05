"""
Permission classes for the transactions app.

Reuses role logic from projects.permissions; adds Shareholder filter enforcement.
"""
from rest_framework import permissions

from projects.models import Stakeholder
from projects.permissions import get_stakeholder_role


class TransactionPermission(permissions.BasePermission):
    """
    - Owner / Collaborator : full CRUD.
    - Observer             : read-only.
    - Shareholder          : read-only, and queryset is filtered by the view.
    - Non-member           : no access.
    """

    message = "You do not have permission to perform this action on this project's transactions."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        project = obj.project
        role = get_stakeholder_role(request.user, project)

        if role is None:
            return False

        # All roles can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only Owner and Collaborator can write
        return role in (Stakeholder.Role.OWNER, Stakeholder.Role.COLLABORATOR)


class RecurringTransactionPermission(permissions.BasePermission):
    """Only Owner and Collaborator can manage recurring transaction templates."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        project = obj.project
        role = get_stakeholder_role(request.user, project)
        if request.method in permissions.SAFE_METHODS:
            return role is not None
        return role in (Stakeholder.Role.OWNER, Stakeholder.Role.COLLABORATOR)
