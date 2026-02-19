# reflections/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import RetrospectiveAsset

@receiver(post_delete, sender=RetrospectiveAsset)
def delete_asset_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
