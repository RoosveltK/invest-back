"""
Tests for the role-based permission matrix.

Covers:
  - Observer: read-only (cannot POST/PATCH/DELETE).
  - Collaborator: can create transactions and stakeholders.
  - Owner: can change project status; others cannot.
  - Shareholder: can only see their own income; blocked from expenses.
  - Non-member: no access.
"""
import pytest
from django.urls import reverse

from projects.models import Project, Stakeholder
from tests.factories import StakeholderFactory, TransactionFactory


@pytest.mark.django_db
class TestObserverReadOnly:
    def test_observer_can_list_transactions(self, observer_client, setup_roles, project):
        url = f"/api/transactions/?project={project.id}"
        resp = observer_client.get(url)
        assert resp.status_code == 200

    def test_observer_cannot_create_transaction(self, observer_client, setup_roles, project):
        url = "/api/transactions/"
        data = {
            "project": project.id,
            "transaction_type": "Expense",
            "amount": "100.00",
            "category": "Tools",
        }
        resp = observer_client.post(url, data, format="json")
        assert resp.status_code == 403

    def test_observer_cannot_delete_transaction(self, observer_client, setup_roles, project, observer_user):
        transaction = TransactionFactory(project=project, author=observer_user)
        url = f"/api/transactions/{transaction.id}/"
        resp = observer_client.delete(url)
        assert resp.status_code == 403


@pytest.mark.django_db
class TestCollaboratorAccess:
    def test_collaborator_can_create_transaction(self, collaborator_client, setup_roles, project):
        url = "/api/transactions/"
        data = {
            "project": project.id,
            "transaction_type": "Expense",
            "amount": "250.00",
            "category": "Software",
        }
        resp = collaborator_client.post(url, data, format="json")
        assert resp.status_code == 201, resp.data

    def test_collaborator_can_add_stakeholder(self, collaborator_client, setup_roles, project):
        url = f"/api/projects/{project.id}/stakeholders/"
        data = {
            "first_name": "Ghost",
            "last_name": "User",
            "email": "ghost@example.com",
            "role": Stakeholder.Role.OBSERVER,
        }
        resp = collaborator_client.post(url, data, format="json")
        assert resp.status_code == 201, resp.data


@pytest.mark.django_db
class TestOwnerControl:
    def test_owner_can_close_project(self, owner_client, project):
        url = f"/api/projects/{project.id}/close/"
        resp = owner_client.post(url)
        assert resp.status_code == 200
        project.refresh_from_db()
        assert project.status == Project.Status.COMPLETED

    def test_collaborator_cannot_close_project(self, collaborator_client, setup_roles, project):
        url = f"/api/projects/{project.id}/close/"
        resp = collaborator_client.post(url)
        assert resp.status_code == 403

    def test_observer_cannot_change_status(self, observer_client, setup_roles, project):
        url = f"/api/projects/{project.id}/pause/"
        resp = observer_client.post(url)
        assert resp.status_code == 403

    def test_non_member_has_no_access(self, other_client, project):
        url = f"/api/projects/{project.id}/"
        resp = other_client.get(url)
        assert resp.status_code == 404  # filtered from queryset


@pytest.mark.django_db
class TestShareholderFilter:
    def test_shareholder_cannot_see_expenses(
        self, shareholder_client, shareholder_user, setup_roles, project
    ):
        TransactionFactory(project=project, transaction_type="Expense", amount="500.00")
        url = "/api/transactions/"
        resp = shareholder_client.get(url)
        assert resp.status_code == 200
        types_returned = [t["transaction_type"] for t in resp.data.get("results", [])]
        assert "Expense" not in types_returned, "Shareholder must not see expense transactions"

    def test_shareholder_sees_own_income(
        self, shareholder_client, shareholder_user, setup_roles, project
    ):
        # Create a stakeholder record for the shareholder
        sh = Stakeholder.objects.get(user=shareholder_user, project=project)
        income = TransactionFactory(
            project=project,
            transaction_type="Income",
            amount="1000.00",
            author=shareholder_user,
            stakeholder_author=sh,
        )
        url = "/api/transactions/"
        resp = shareholder_client.get(url)
        assert resp.status_code == 200
        ids = [t["id"] for t in resp.data.get("results", [])]
        assert income.id in ids

    def test_shareholder_cannot_see_other_incomes(
        self, shareholder_client, shareholder_user, setup_roles, project, collaborator_user
    ):
        collab_sh = Stakeholder.objects.get(user=collaborator_user, project=project)
        other_income = TransactionFactory(
            project=project,
            transaction_type="Income",
            amount="999.00",
            author=collaborator_user,
            stakeholder_author=collab_sh,
        )
        url = "/api/transactions/"
        resp = shareholder_client.get(url)
        assert resp.status_code == 200
        ids = [t["id"] for t in resp.data.get("results", [])]
        assert other_income.id not in ids
