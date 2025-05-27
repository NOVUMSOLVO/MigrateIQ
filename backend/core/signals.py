from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AuditLog, Tenant

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user creation events."""
    if created:
        AuditLog.objects.create(
            user=instance,
            action='user_created',
            resource_type='user',
            resource_id=str(instance.id),
            metadata={
                'username': instance.username,
                'email': instance.email,
            }
        )


@receiver(post_save, sender=Tenant)
def log_tenant_changes(sender, instance, created, **kwargs):
    """Log tenant creation and updates."""
    action = 'tenant_created' if created else 'tenant_updated'
    
    AuditLog.objects.create(
        tenant=instance,
        action=action,
        resource_type='tenant',
        resource_id=str(instance.id),
        metadata={
            'name': instance.name,
            'slug': instance.slug,
            'plan': instance.plan,
        }
    )


@receiver(post_delete, sender=Tenant)
def log_tenant_deletion(sender, instance, **kwargs):
    """Log tenant deletion."""
    AuditLog.objects.create(
        action='tenant_deleted',
        resource_type='tenant',
        resource_id=str(instance.id),
        metadata={
            'name': instance.name,
            'slug': instance.slug,
        }
    )