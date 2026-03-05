"""Django admin registrations for the projects app."""
from django.contrib import admin

from projects.models import Project, Stakeholder


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "project_type", "status", "owner", "start_date", "initial_budget"]
    list_filter = ["status", "project_type"]
    search_fields = ["name", "owner__email"]
    raw_id_fields = ["owner"]


@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "role", "project"]
    list_filter = ["role"]
    search_fields = ["email", "first_name", "last_name"]
    raw_id_fields = ["user", "project"]
