from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ml.cache import bump_buster

from .models import Product


@receiver(post_save, sender=Product)
def _on_product_save(sender, instance, **kwargs):
    bump_buster()


@receiver(post_delete, sender=Product)
def _on_product_delete(sender, instance, **kwargs):
    bump_buster()
