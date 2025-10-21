from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Filiere(models.Model):
    """Filières d'études (ex: Génie Informatique, Génie Civil, etc.)"""
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"


class Niveau(models.Model):
    """Niveaux d'études (ex: Licence 1, Licence 2, Master 1, etc.)"""
    CYCLES = [
        ('L', 'Licence'),
        ('M', 'Master'),
        ('D', 'Doctorat'),
    ]
    
    nom = models.CharField(max_length=50)
    cycle = models.CharField(max_length=1, choices=CYCLES)
    annee = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    
    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"
        ordering = ['cycle', 'annee']
        unique_together = ['cycle', 'annee']
    
    def __str__(self):
        return f"{self.get_cycle_display()} {self.annee}"


class Etudiant(models.Model):
    """Informations sur les étudiants"""
    matricule = models.CharField(max_length=20, unique=True, verbose_name="Matricule")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name='etudiants', verbose_name="Filière")
    niveau = models.ForeignKey(Niveau, on_delete=models.PROTECT, related_name='etudiants', verbose_name="Niveau")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lieu de naissance")
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True, null=True)
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    date_inscription = models.DateField(auto_now_add=True, verbose_name="Date d'inscription")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    photo = models.ImageField(upload_to='etudiants/photos/', blank=True, null=True, verbose_name="Photo")
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"
    
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
    
    def get_taux_presence(self):
        """Calcule le taux de présence de l'étudiant"""
        from attendance.models import Presence
        total = self.presences.count()
        if total == 0:
            return 0
        presents = self.presences.filter(statut__in=['P', 'R']).count()
        return round((presents / total) * 100, 2)