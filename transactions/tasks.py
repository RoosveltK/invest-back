"""
Celery tasks for the transactions app.

generate_recurring_transactions:
  - Daily cron job (Celery Beat) that checks RecurringTransaction rules
    and creates Transaction entries for any that are due today.
  - Skips inactive rules or rules linked to locked projects.

send_email_async:
  - Generic async email sending to avoid blocking the request cycle.
"""
import logging
from datetime import date, timedelta

from celery import shared_task
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _next_occurrence(last_date: date, frequency: str) -> date:
    """Return the next occurrence date from last_date based on frequency."""
    freq_map = {
        "Daily": timedelta(days=1),
        "Weekly": timedelta(weeks=1),
        "Monthly": None,  # handled separately
        "Yearly": None,  # handled separately
    }
    if frequency == "Monthly":
        # Add one month (approximate: same day next month)
        month = last_date.month + 1
        year = last_date.year + (month > 12)
        month = month if month <= 12 else month - 12
        day = min(last_date.day, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    if frequency == "Yearly":
        return date(last_date.year + 1, last_date.month, last_date.day)
    return last_date + freq_map[frequency]


@shared_task(bind=True, name="transactions.tasks.generate_recurring_transactions")
def generate_recurring_transactions(self):
    """
    Daily Celery Beat task:
      1. Fetch all active RecurringTransaction rules whose projects are Ongoing.
      2. For each rule, generate Transaction entries for every missed occurrence up to today.
      3. Update last_generated.
    """
    from transactions.models import RecurringTransaction, Transaction

    today = date.today()
    created_count = 0

    rules = (
        RecurringTransaction.objects
        .filter(is_active=True, project__status="Ongoing")
        .select_related("project")
    )

    for rule in rules:
        # Determine starting point
        last = rule.last_generated or (rule.start_date - timedelta(days=1))
        next_due = _next_occurrence(last, rule.frequency)

        while next_due <= today:
            # Stop if past end_date
            if rule.end_date and next_due > rule.end_date:
                rule.is_active = False
                rule.save(update_fields=["is_active"])
                break

            Transaction.objects.create(
                project=rule.project,
                transaction_type=rule.transaction_type,
                amount=rule.amount,
                category=rule.category,
                description=f"[Auto] {rule.description}",
                author=None,
            )
            created_count += 1
            last = next_due
            next_due = _next_occurrence(last, rule.frequency)

        if rule.last_generated != last:
            rule.last_generated = last
            rule.save(update_fields=["last_generated"])

    logger.info("generate_recurring_transactions: created %d transactions.", created_count)
    return {"created": created_count}


@shared_task(bind=True, name="transactions.tasks.send_email_async")
def send_email_async(self, subject: str, message: str, recipient_list: list, html_message: str = None):
    """Asynchronously send a plain-text (and optional HTML) email via Django's email backend."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Email sent to %s: %s", recipient_list, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipient_list, exc)
        raise self.retry(exc=exc, countdown=60, max_retries=3)
