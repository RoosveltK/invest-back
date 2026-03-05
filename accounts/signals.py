"""
Django signals for the accounts app.

Key signal: when a CustomUser is activated (is_email_verified=True),
automatically link any 'ghost' Stakeholder records that match by email.
"""
from allauth.account.signals import email_confirmed
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomUser

@receiver(email_confirmed)
def set_email_verified_on_confirmation(request, email_address, **kwargs):
    """
    When allauth confirms an email address, update our custom user model field.
    """
    user = email_address.user
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])


@receiver(post_save, sender=CustomUser)
def link_ghost_stakeholders(sender, instance, created, **kwargs):
    """
    When a user account becomes email-verified, find any Stakeholder records
    that share the same email and have no user linked yet ('ghosts'),
    and assign this user to them.
    """
    if instance.is_email_verified:
        # Avoid circular import by importing here
        from projects.models import Stakeholder

        ghost_stakeholders = Stakeholder.objects.filter(
            email=instance.email,
            user__isnull=True,
        )
        if ghost_stakeholders.exists():
            ghost_stakeholders.update(user=instance)
