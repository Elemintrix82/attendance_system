from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profil


@receiver(post_save, sender=User)
def create_user_profil(sender, instance, created, **kwargs):
    """
    Créer automatiquement un Profil quand un User est créé
    """
    if created:
        Profil.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profil(sender, instance, **kwargs):
    """
    Sauvegarder le Profil quand le User est sauvegardé
    """
    if hasattr(instance, 'profil'):
        instance.profil.save()
    else:
        # Si le profil n'existe pas, le créer
        Profil.objects.create(user=instance)