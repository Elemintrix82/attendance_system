from django.db import models
from django.contrib.auth.models import User


class Profil(models.Model):
    """Profil utilisateur étendu pour l'administration"""
    ROLES = [
        ('ADMIN', 'Administrateur'),
        ('ENSEIGNANT', 'Enseignant'),
        ('SCOLARITE', 'Service Scolarité'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, 
                               related_name='profil',
                               verbose_name="Utilisateur")
    role = models.CharField(max_length=20, choices=ROLES, 
                           default='ENSEIGNANT',
                           verbose_name="Rôle")
    telephone = models.CharField(max_length=20, blank=True, null=True, 
                                verbose_name="Téléphone")
    photo = models.ImageField(upload_to='profils/photos/', 
                             blank=True, null=True,
                             verbose_name="Photo")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    def est_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == 'ADMIN' or self.user.is_superuser
    
    def est_enseignant(self):
        """Vérifie si l'utilisateur est enseignant"""
        return self.role == 'ENSEIGNANT'
    
    def est_scolarite(self):
        """Vérifie si l'utilisateur est du service scolarité"""
        return self.role == 'SCOLARITE'


class HistoriqueConnexion(models.Model):
    """Historique des connexions des utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            related_name='historique_connexions',
                            verbose_name="Utilisateur")
    date_connexion = models.DateTimeField(auto_now_add=True, 
                                         verbose_name="Date de connexion")
    ip_address = models.GenericIPAddressField(blank=True, null=True, 
                                             verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, null=True, 
                                  verbose_name="User Agent")
    
    class Meta:
        verbose_name = "Historique de connexion"
        verbose_name_plural = "Historiques de connexion"
        ordering = ['-date_connexion']
    
    def __str__(self):
        return f"{self.user.username} - {self.date_connexion}"