from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Filiere, Niveau
from teachers.models import Enseignant


class Salle(models.Model):
    """Salles de classe"""
    TYPES_SALLE = [
        ('AMPHI', 'Amphithéâtre'),
        ('TD', 'Salle de TD'),
        ('TP', 'Salle de TP'),
        ('LAB', 'Laboratoire'),
    ]
    
    nom = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    type_salle = models.CharField(max_length=10, choices=TYPES_SALLE, verbose_name="Type de salle")
    capacite = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Capacité")
    batiment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Bâtiment")
    etage = models.IntegerField(blank=True, null=True, verbose_name="Étage")
    equipements = models.TextField(blank=True, null=True, 
                                   help_text="Projecteur, Tableau, Ordinateurs, etc.",
                                   verbose_name="Équipements")
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"
        ordering = ['batiment', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_salle_display()})"


class Cours(models.Model):
    """Cours dispensés"""
    SEMESTRES = [
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    ]
    
    JOURS_SEMAINE = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
    ]
    
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    intitule = models.CharField(max_length=200, verbose_name="Intitulé")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name='cours', verbose_name="Filière")
    niveau = models.ForeignKey(Niveau, on_delete=models.PROTECT, related_name='cours', verbose_name="Niveau")
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, 
                                   related_name='cours', verbose_name="Enseignant")
    salle = models.ForeignKey(Salle, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='cours', verbose_name="Salle")
    semestre = models.IntegerField(choices=SEMESTRES, verbose_name="Semestre")
    annee_academique = models.CharField(max_length=9, help_text="Ex: 2024-2025", 
                                       verbose_name="Année académique")
    
    # Horaires
    jour_semaine = models.CharField(max_length=10, choices=JOURS_SEMAINE, blank=True, null=True,
                                     verbose_name="Jour de la semaine")
    heure_debut = models.TimeField(blank=True, null=True, verbose_name="Heure de début")
    heure_fin = models.TimeField(blank=True, null=True, verbose_name="Heure de fin")
    
    # Crédits et coefficients
    credits = models.IntegerField(default=3, validators=[MinValueValidator(1)], verbose_name="Crédits")
    coefficient = models.DecimalField(max_digits=3, decimal_places=1, default=1.0, verbose_name="Coefficient")
    
    # Volume horaire
    volume_horaire_cm = models.IntegerField(default=0, verbose_name="Volume horaire CM (heures)")
    volume_horaire_td = models.IntegerField(default=0, verbose_name="Volume horaire TD (heures)")
    volume_horaire_tp = models.IntegerField(default=0, verbose_name="Volume horaire TP (heures)")
    
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['filiere', 'niveau', 'code']
        unique_together = ['code', 'annee_academique']
    
    def __str__(self):
        return f"{self.code} - {self.intitule}"
    
    def get_volume_horaire_total(self):
        """Calcule le volume horaire total"""
        return self.volume_horaire_cm + self.volume_horaire_td + self.volume_horaire_tp
    
    def get_nombre_seances(self):
        """Retourne le nombre de séances"""
        return self.seances.count()


class SeanceCours(models.Model):
    """Séances de cours (chaque séance peut avoir une présence)"""
    TYPE_SEANCE = [
        ('CM', 'Cours Magistral'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
        ('EXAM', 'Examen'),
        ('CONTROLE', 'Contrôle Continu'),
    ]
    
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='seances', verbose_name="Cours")
    date = models.DateField(verbose_name="Date")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    salle = models.ForeignKey(Salle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Salle")
    type_seance = models.CharField(max_length=20, choices=TYPE_SEANCE, default='CM', verbose_name="Type de séance")
    contenu = models.TextField(blank=True, null=True, 
                               help_text="Résumé du contenu de la séance",
                               verbose_name="Contenu")
    presente = models.BooleanField(default=False, 
                                   help_text="La présence a-t-elle été faite?",
                                   verbose_name="Présence effectuée")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Séance de cours"
        verbose_name_plural = "Séances de cours"
        ordering = ['-date', '-heure_debut']
        unique_together = ['cours', 'date', 'heure_debut']
    
    def __str__(self):
        return f"{self.cours.code} - {self.date} ({self.get_type_seance_display()})"
    
    def get_taux_presence(self):
        """Calcule le taux de présence pour cette séance"""
        from attendance.models import Presence
        total = self.presences.count()
        if total == 0:
            return 0
        presents = self.presences.filter(statut__in=['P', 'R']).count()
        return round((presents / total) * 100, 2)
    
    def get_nombre_presents(self):
        """Nombre d'étudiants présents"""
        return self.presences.filter(statut__in=['P', 'R']).count()
    
    def get_nombre_absents(self):
        """Nombre d'étudiants absents"""
        return self.presences.filter(statut='A').count()