"""
Projects app models:
  - Project: the core investment/subscription entity.
  - Stakeholder: project members, including 'ghost' (user=None) stakeholders.
"""
from django.conf import settings
from django.db import models


class Project(models.Model):
    class ProjectType(models.TextChoices):
        INVESTMENT = "Investment", "Investment"
        SUBSCRIPTION = "Subscription", "Subscription"

    class Status(models.TextChoices):
        ONGOING = "Ongoing", "Ongoing"
        COMPLETED = "Completed", "Completed"
        PAUSED = "Paused", "Paused"
        ABANDONED = "Abandoned", "Abandoned"

    name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    tag = models.CharField(max_length=100, blank=True)
    initial_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    documents = models.FileField(upload_to="projects/documents/", null=True, blank=True)
    photos = models.ImageField(upload_to="projects/photos/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} ({self.project_type})"

    @property
    def is_locked(self):
        """Returns True when the project no longer accepts new transactions."""
        return self.status in (
            self.Status.COMPLETED,
            self.Status.PAUSED,
            self.Status.ABANDONED,
        )

    @property
    def total_expenses(self):
        return (
            self.transactions.filter(transaction_type="Expense").
            aggregate(total=models.Sum("amount"))["total"] or 0
        )

    @property
    def total_income(self):
        return (
            self.transactions.filter(transaction_type="Income").
            aggregate(total=models.Sum("amount"))["total"] or 0
        )

    @property
    def remaining_budget(self):
        """initial_budget reduced by expenses only (can go negative)."""
        return self.initial_budget - self.total_expenses


class Stakeholder(models.Model):
    class Role(models.TextChoices):
        SUPER_ADMIN = "Super-admin", "Super-admin"
        OWNER = "Owner", "Owner"
        COLLABORATOR = "Collaborator", "Collaborator"
        OBSERVER = "Observer", "Observer"
        SHAREHOLDER = "Shareholder", "Shareholder"

    # user can be null for "ghost" stakeholders (invited by email before account creation)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stakeholder_profiles",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="stakeholders",
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OBSERVER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        unique_together = [("project", "email")]
        verbose_name = "Stakeholder"
        verbose_name_plural = "Stakeholders"

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.role} on {self.project}"
