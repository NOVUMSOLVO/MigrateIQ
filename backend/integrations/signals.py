"""
Signal handlers for integrations app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation events."""
    if created:
        # Placeholder for user creation logic
        pass


@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    """Handle user deletion events."""
    # Placeholder for user deletion logic
    pass
