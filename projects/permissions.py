"""
Permission classes for the projects app.

Permission Matrix:
  - Super-admin : Django staff/superuser — manages accounts, not business data.
  - Owner       : Full project control (CRUD, status changes).
  - Collaborator: Manage transactions and stakeholders (no status change).
  - Observer    : Read-only access to everything in the project.
  - Shareholder : Strictly filtered — can only see their own income/dividends.

Helper function `get_stakeholder_role` is shared with the transactions app.
"""
from rest_framework import permissions

from projects.models import Stakeholder


def get_stakeholder_role(user, project):
    """Return the role string for a user on a given project, or None."""
    try:
        sh = Stakeholder.objects.get(user=user, project=project)
        return sh.role
    except Stakeholder.DoesNotExist:
        return None


class IsProjectMember(permissions.BasePermission):
    """Allow access only to users who are stakeholders of the project."""

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, "stakeholders") else obj.project
        return Stakeholder.objects.filter(user=request.user, project=project).exists()


class IsProjectOwner(permissions.BasePermission):
    """Allow access only to project Owners."""

    message = "Only project Owners can perform this action."

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, "stakeholders") else obj.project
        role = get_stakeholder_role(request.user, project)
        return role == Stakeholder.Role.OWNER


class IsOwnerOrCollaborator(permissions.BasePermission):
    """Allow Owners and Collaborators to write; Observers and Shareholders read-only."""

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, "stakeholders") else obj.project
        role = get_stakeholder_role(request.user, project)
        if request.method in permissions.SAFE_METHODS:
            return role in (
                Stakeholder.Role.OWNER,
                Stakeholder.Role.COLLABORATOR,
                Stakeholder.Role.OBSERVER,
                Stakeholder.Role.SHAREHOLDER,
            )
        return role in (Stakeholder.Role.OWNER, Stakeholder.Role.COLLABORATOR)


class IsObserverOrAbove(permissions.BasePermission):
    """Allow read access to all roles."""

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, "stakeholders") else obj.project
        role = get_stakeholder_role(request.user, project)
        return role is not None


class IsShareholderFiltered(permissions.BasePermission):
    """
    Shareholders can only view their own income transactions.
    This class is used as a guard — actual queryset filtering is done in the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
