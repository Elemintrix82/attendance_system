from django.db import models
from django.contrib.auth.models import User


class Enseignant(models.Model):
    """Informations sur les enseignants"""
    GRADES = [
        ('ASSISTANT', 'Assistant'),
        ('CHARGE', 'Chargé de cours'),
        ('MAITRE_ASSISTANT', 'Maître Assistant'),
        ('MAITRE_CONFERENCE', 'Maître de Conférences'),
        ('PROFESSEUR', 'Professeur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='enseignant', verbose_name="Utilisateur")
    matricule = models.CharField(max_length=20, unique=True, verbose_name="Matricule")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(unique=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    specialite = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité")
    grade = models.CharField(max_length=20, choices=GRADES, blank=True, null=True, verbose_name="Grade")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True, null=True)
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    date_embauche = models.DateField(blank=True, null=True, verbose_name="Date d'embauche")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    photo = models.ImageField(upload_to='enseignants/photos/', blank=True, null=True, verbose_name="Photo")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"
    
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
    
    def get_nombre_cours(self):
        """Retourne le nombre de cours assignés"""
        return self.cours.filter(actif=True).count()