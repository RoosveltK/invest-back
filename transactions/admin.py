"""Django admin registrations for the transactions app."""
from django.contrib import admin

from transactions.models import RecurringTransaction, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["project", "transaction_type", "amount", "category", "author", "created_at"]
    list_filter = ["transaction_type", "category"]
    search_fields = ["project__name", "author__email", "category"]
    raw_id_fields = ["project", "author", "stakeholder_author"]
    date_hierarchy = "created_at"


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ["project", "transaction_type", "amount", "frequency", "is_active", "last_generated"]
    list_filter = ["frequency", "transaction_type", "is_active"]
    search_fields = ["project__name"]
    raw_id_fields = ["project"]
