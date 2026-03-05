"""
Tests for project-level business logic.

Covers:
  - close() action forces status = Completed.
  - Pausing and abandoning a project suspends active RecurringTransactions.
  - Completed project cannot be reopened.
  - Ghost stakeholder auto-link signal on user email verification.
  - CRUD basics for projects filtered to member only.
"""
import pytest
from decimal import Decimal

from projects.models import Project, Stakeholder
from transactions.models import RecurringTransaction
from tests.factories import (
    ProjectFactory,
    RecurringTransactionFactory,
    StakeholderFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestCloseProject:
    def test_close_sets_completed_status(self, owner_client, project):
        url = f"/api/projects/{project.id}/close/"
        resp = owner_client.post(url)
        assert resp.status_code == 200
        project.refresh_from_db()
        assert project.status == Project.Status.COMPLETED

    def test_close_suspends_recurring_transactions(self, owner_client, project):
        rule = RecurringTransactionFactory(project=project, is_active=True)
        url = f"/api/projects/{project.id}/close/"
        owner_client.post(url)
        rule.refresh_from_db()
        assert not rule.is_active

    def test_completed_project_cannot_be_reopened(self, owner_client, project):
        project.status = Project.Status.COMPLETED
        project.save()
        url = f"/api/projects/{project.id}/reopen/"
        resp = owner_client.post(url)
        assert resp.status_code == 400

    def test_pause_suspends_recurring_transactions(self, owner_client, project):
        rule = RecurringTransactionFactory(project=project, is_active=True)
        url = f"/api/projects/{project.id}/pause/"
        owner_client.post(url)
        rule.refresh_from_db()
        assert not rule.is_active

    def test_reopen_paused_project(self, owner_client, project):
        project.status = Project.Status.PAUSED
        project.save()
        url = f"/api/projects/{project.id}/reopen/"
        resp = owner_client.post(url)
        assert resp.status_code == 200
        project.refresh_from_db()
        assert project.status == Project.Status.ONGOING


@pytest.mark.django_db
class TestGhostStakeholder:
    def test_ghost_stakeholder_linked_on_email_verification(self, db):
        """
        Given a ghost Stakeholder (user=None) with email X,
        when a CustomUser with email X is saved with is_email_verified=True,
        the Stakeholder.user field should be automatically populated.
        """
        project = ProjectFactory()
        ghost_email = "ghost@example.com"

        # Create ghost stakeholder
        ghost = StakeholderFactory(
            user=None,
            project=project,
            email=ghost_email,
            first_name="Ghost",
            last_name="Invited",
        )
        assert ghost.user is None

        # Create and activate user
        user = UserFactory(email=ghost_email, is_email_verified=False)
        assert Stakeholder.objects.get(pk=ghost.pk).user is None  # still ghost

        # Verify email — triggers signal
        user.is_email_verified = True
        user.save()

        ghost.refresh_from_db()
        assert ghost.user == user, "Ghost stakeholder should be linked to the newly verified user"

    def test_ghost_not_linked_if_email_not_verified(self, db):
        ghost_email = "unverified@example.com"
        project = ProjectFactory()
        ghost = StakeholderFactory(user=None, project=project, email=ghost_email)

        user = UserFactory(email=ghost_email, is_email_verified=False)
        ghost.refresh_from_db()
        assert ghost.user is None


@pytest.mark.django_db
class TestProjectMembershipFilter:
    def test_owner_sees_own_projects(self, owner_client, project):
        resp = owner_client.get("/api/projects/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.data.get("results", [])]
        assert project.id in ids

    def test_non_member_cannot_see_project(self, other_client, project):
        resp = other_client.get(f"/api/projects/{project.id}/")
        assert resp.status_code == 404

    def test_project_create_adds_owner_stakeholder(self, owner_client, owner_user):
        data = {
            "name": "New Fund",
            "project_type": "Investment",
            "start_date": "2025-01-01",
            "initial_budget": "50000.00",
        }
        resp = owner_client.post("/api/projects/", data, format="json")
        assert resp.status_code == 201
        project_id = resp.data["id"]
        assert Stakeholder.objects.filter(
            project_id=project_id,
            user=owner_user,
            role=Stakeholder.Role.OWNER,
        ).exists()
