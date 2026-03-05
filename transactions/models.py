"""
Transactions app models:
  - Transaction     : a single income or expense entry on a project.
  - RecurringTransaction: a scheduled rule for auto-generating Transactions.
"""
from django.conf import settings
from django.db import models

from projects.models import Project


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        EXPENSE = "Expense", "Expense"
        INCOME = "Income", "Income"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    # stakeholder author — supports ghost stakeholders
    stakeholder_author = models.ForeignKey(
        "projects.Stakeholder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.transaction_type} {self.amount} on {self.project}"

    def save(self, *args, **kwargs):
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive.")
        super().save(*args, **kwargs)


class RecurringTransaction(models.Model):
    class TransactionType(models.TextChoices):
        EXPENSE = "Expense", "Expense"
        INCOME = "Income", "Income"

    class Frequency(models.TextChoices):
        DAILY = "Daily", "Daily"
        WEEKLY = "Weekly", "Weekly"
        MONTHLY = "Monthly", "Monthly"
        YEARLY = "Yearly", "Yearly"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="recurring_transactions",
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Celery Beat tracking
    last_generated = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recurring Transaction"
        verbose_name_plural = "Recurring Transactions"

    def __str__(self):
        return f"{self.frequency} {self.transaction_type} {self.amount} on {self.project}"
