"""URL routes for the transactions app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from transactions.views import RecurringTransactionViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r"recurring", RecurringTransactionViewSet, basename="recurring-transaction")
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
]
