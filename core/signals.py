from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

from core.models import Profile, Supplier

@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

        
@receiver(post_save, sender=Supplier)
def create_profile(sender, instance, created, **kwargs):
    if created:
        user = get_user_model().objects.create(username=instance.id_supplier)
        user.set_password(user.username)
        user.save()
        supplier = Supplier.objects.get(id=instance.id)
        supplier.account = user
        supplier.save()

