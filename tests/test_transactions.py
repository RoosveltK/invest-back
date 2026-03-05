"""
Tests for transaction business logic.

Covers:
  - Budget reduction on expense (and that it can go negative).
  - Income does NOT affect the budget.
  - Locked project (Completed/Paused/Abandoned) blocks new transactions.
  - Recurring transaction generation via Celery task.
  - Paused project suspends recurring generation.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from projects.models import Project
from transactions.models import RecurringTransaction, Transaction
from tests.factories import (
    ProjectFactory,
    RecurringTransactionFactory,
    StakeholderFactory,
    TransactionFactory,
    UserFactory,
)
from projects.models import Stakeholder


@pytest.mark.django_db
class TestBudgetLogic:
    def test_expense_reduces_remaining_budget(self):
        project = ProjectFactory(initial_budget=Decimal("1000.00"))
        TransactionFactory(
            project=project, transaction_type="Expense", amount=Decimal("300.00")
        )
        assert project.remaining_budget == Decimal("700.00")

    def test_budget_can_go_negative(self):
        project = ProjectFactory(initial_budget=Decimal("100.00"))
        TransactionFactory(
            project=project, transaction_type="Expense", amount=Decimal("500.00")
        )
        assert project.remaining_budget == Decimal("-400.00")

    def test_income_does_not_affect_budget(self):
        project = ProjectFactory(initial_budget=Decimal("1000.00"))
        TransactionFactory(
            project=project, transaction_type="Income", amount=Decimal("5000.00")
        )
        # Budget should still be 1000 (no expenses deducted)
        assert project.remaining_budget == Decimal("1000.00")

    def test_multiple_expenses_accumulate(self):
        project = ProjectFactory(initial_budget=Decimal("500.00"))
        TransactionFactory(project=project, transaction_type="Expense", amount=Decimal("200.00"))
        TransactionFactory(project=project, transaction_type="Expense", amount=Decimal("150.00"))
        assert project.remaining_budget == Decimal("150.00")


@pytest.mark.django_db
class TestLockedProject:
    """Transactions cannot be created on Completed, Paused, or Abandoned projects."""

    def _assert_create_blocked(self, client, project):
        url = "/api/transactions/"
        data = {
            "project": project.id,
            "transaction_type": "Expense",
            "amount": "50.00",
        }
        resp = client.post(url, data, format="json")
        assert resp.status_code in (400, 403), (
            f"Expected 400/403 for locked project, got {resp.status_code}: {resp.data}"
        )

    def test_completed_project_blocks_transaction(self, owner_client, project):
        project.status = Project.Status.COMPLETED
        project.save()
        self._assert_create_blocked(owner_client, project)

    def test_paused_project_blocks_transaction(self, owner_client, project):
        project.status = Project.Status.PAUSED
        project.save()
        self._assert_create_blocked(owner_client, project)

    def test_abandoned_project_blocks_transaction(self, owner_client, project):
        project.status = Project.Status.ABANDONED
        project.save()
        self._assert_create_blocked(owner_client, project)

    def test_ongoing_project_allows_transaction(self, collaborator_client, setup_roles, project):
        assert project.status == Project.Status.ONGOING
        url = "/api/transactions/"
        data = {
            "project": project.id,
            "transaction_type": "Expense",
            "amount": "50.00",
        }
        resp = collaborator_client.post(url, data, format="json")
        assert resp.status_code == 201


@pytest.mark.django_db
class TestRecurringGeneration:
    def test_task_creates_transaction_for_due_rule(self):
        from transactions.tasks import generate_recurring_transactions

        project = ProjectFactory(status=Project.Status.ONGOING)
        rule = RecurringTransactionFactory(
            project=project,
            frequency="Monthly",
            start_date=date.today() - timedelta(days=32),
            last_generated=date.today() - timedelta(days=32),
            is_active=True,
        )
        initial_count = Transaction.objects.filter(project=project).count()
        generate_recurring_transactions.apply()
        assert Transaction.objects.filter(project=project).count() > initial_count

    def test_paused_project_suspends_generation(self):
        from transactions.tasks import generate_recurring_transactions

        project = ProjectFactory(status=Project.Status.PAUSED)
        RecurringTransactionFactory(
            project=project,
            frequency="Daily",
            start_date=date.today() - timedelta(days=5),
            last_generated=date.today() - timedelta(days=5),
            is_active=True,
        )
        initial_count = Transaction.objects.filter(project=project).count()
        generate_recurring_transactions.apply()
        assert Transaction.objects.filter(project=project).count() == initial_count

    def test_expired_rule_is_deactivated(self):
        from transactions.tasks import generate_recurring_transactions

        project = ProjectFactory(status=Project.Status.ONGOING)
        rule = RecurringTransactionFactory(
            project=project,
            frequency="Daily",
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
            last_generated=date.today() - timedelta(days=6),
            is_active=True,
        )
        generate_recurring_transactions.apply()
        rule.refresh_from_db()
        assert not rule.is_active
