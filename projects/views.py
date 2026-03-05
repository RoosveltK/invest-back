"""
Views for the projects app.

ProjectViewSet:
  - Standard CRUD scoped to projects the user is a member of.
  - Extra actions: close, pause, abandon, reopen (owner only).
  - Status changes suspend RecurringTransactions automatically.

StakeholderViewSet:
  - Scoped to a specific project.
  - Respects permission matrix.
"""
import asyncio

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from projects.models import Project, Stakeholder
from projects.permissions import IsOwnerOrCollaborator, IsProjectOwner, get_stakeholder_role
from projects.serializers import (
    ProjectSerializer,
    ProjectStatusSerializer,
    StakeholderSerializer,
)


def _broadcast_project_update(project_id: int, event_type: str, data: dict):
    """Fire-and-forget WebSocket broadcast from a sync context."""
    try:
        from realtime.consumers import ProjectConsumer
        asyncio.run(ProjectConsumer.broadcast_update(project_id, {"type": event_type, **data}))
    except Exception:
        pass  # Never let broadcast failure break the API response


@extend_schema_view(
    list=extend_schema(summary="List projects for the authenticated user", tags=["projects"]),
    create=extend_schema(summary="Create a new project", tags=["projects"]),
    retrieve=extend_schema(summary="Get project details", tags=["projects"]),
    update=extend_schema(summary="Update a project", tags=["projects"]),
    partial_update=extend_schema(summary="Partially update a project", tags=["projects"]),
    destroy=extend_schema(summary="Delete a project", tags=["projects"]),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for projects.
    List is scoped to projects where the authenticated user is a stakeholder.
    """

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            stakeholders__user=self.request.user
        ).distinct().select_related("owner")

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        # Automatically add the creator as Owner stakeholder
        Stakeholder.objects.create(
            user=self.request.user,
            project=project,
            first_name=self.request.user.first_name,
            last_name=self.request.user.last_name,
            email=self.request.user.email,
            role=Stakeholder.Role.OWNER,
        )
        _broadcast_project_update(project.id, "project.created", ProjectSerializer(project).data)

    def perform_update(self, serializer):
        project = serializer.save()
        _broadcast_project_update(project.id, "project.updated", ProjectSerializer(project).data)

    # -------------------------------------------------------------------------
    # Status-change actions (Owner only)
    # -------------------------------------------------------------------------
    def _change_status(self, request, pk, new_status):
        project = self.get_object()
        role = get_stakeholder_role(request.user, project)
        if role != Stakeholder.Role.OWNER:
            return Response(
                {"detail": "Only the project Owner can change the project status."},
                status=status.HTTP_403_FORBIDDEN,
            )
        project.status = new_status
        project.save(update_fields=["status", "updated_at"])

        # Suspend active recurring transactions when project is no longer Ongoing
        if new_status != Project.Status.ONGOING:
            project.recurring_transactions.filter(is_active=True).update(is_active=False)

        _broadcast_project_update(project.id, "project.status_changed", {"status": new_status})
        return Response(ProjectSerializer(project).data)

    @extend_schema(
        summary="Close a project (force status = Completed)",
        tags=["projects"],
        request=None,
        responses={200: ProjectSerializer},
    )
    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        """Force project status to 'Completed'. Suspends recurring transactions."""
        return self._change_status(request, pk, Project.Status.COMPLETED)

    @extend_schema(
        summary="Pause a project",
        tags=["projects"],
        request=None,
        responses={200: ProjectSerializer},
    )
    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        """Set project status to 'Paused'. Suspends recurring transactions."""
        return self._change_status(request, pk, Project.Status.PAUSED)

    @extend_schema(
        summary="Abandon a project",
        tags=["projects"],
        request=None,
        responses={200: ProjectSerializer},
    )
    @action(detail=True, methods=["post"], url_path="abandon")
    def abandon(self, request, pk=None):
        """Set project status to 'Abandoned'. Suspends recurring transactions."""
        return self._change_status(request, pk, Project.Status.ABANDONED)

    @extend_schema(
        summary="Reopen a paused or abandoned project",
        tags=["projects"],
        request=None,
        responses={200: ProjectSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request, pk=None):
        """Set project status back to 'Ongoing'."""
        project = self.get_object()
        if project.status == Project.Status.COMPLETED:
            return Response(
                {"detail": "A completed project cannot be reopened."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._change_status(request, pk, Project.Status.ONGOING)


@extend_schema_view(
    list=extend_schema(summary="List stakeholders of a project", tags=["stakeholders"]),
    create=extend_schema(summary="Add a stakeholder to a project", tags=["stakeholders"]),
    retrieve=extend_schema(summary="Get stakeholder details", tags=["stakeholders"]),
    update=extend_schema(summary="Update a stakeholder", tags=["stakeholders"]),
    partial_update=extend_schema(summary="Partially update a stakeholder", tags=["stakeholders"]),
    destroy=extend_schema(summary="Remove a stakeholder from a project", tags=["stakeholders"]),
)
class StakeholderViewSet(viewsets.ModelViewSet):
    """
    CRUD for stakeholders scoped to a specific project.
    - Owners and Collaborators can write.
    - Observers and Shareholders are read-only.
    """

    serializer_class = StakeholderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrCollaborator]

    def _get_project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_pk"])

    def get_queryset(self):
        project = self._get_project()
        user_role = get_stakeholder_role(self.request.user, project)
        if user_role is None:
            return Stakeholder.objects.none()
        return Stakeholder.objects.filter(project=project).select_related("user")

    def perform_create(self, serializer):
        project = self._get_project()
        if project.is_locked:
            raise serializers.ValidationError(
                "Cannot add stakeholders to a locked project."
            )
        serializer.save(project=project)
