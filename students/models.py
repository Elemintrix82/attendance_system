from django.db import models
from django.core.validators import MinValueValidator
from datetime import datetime


class Filiere(models.Model):
    """
    Filières complètes : Spécialité + Formation + Niveau
    Exemple : Génie Informatique (GI) - Formation Initiale (FI) - Niveau 3
    """
    
    # Spécialités
    SPECIALITES = [
        ('GI', 'Génie Informatique et Télécommunication'),
        ('GLO', 'Génie Logistique'),
        ('GRT', 'Génie des Réseaux et Télécommunications'),
        ('CSCD', 'Cyber-Sécurité et Cryptographie Digitale'),
        ('SSI', 'Systèmes et Sécurité Informatique'),
    ]
    
    # Formations
    FORMATIONS = [
        ('FI', 'Formation Initiale'),
        ('FA', 'Formation en Alternance'),
        ('MP', 'Master Professionnel'),
    ]
    
    # Niveaux
    NIVEAUX = [
        ('N1', 'Niveau 1'),
        ('N2', 'Niveau 2'),
        ('N3', 'Niveau 3'),
        ('N4', 'Niveau 4'),
        ('N5', 'Niveau 5'),
    ]
    
    # Jours de la semaine
    JOURS_SEMAINE = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
    ]
    
    # Champs principaux
    code = models.CharField(max_length=20, unique=True, verbose_name="Code", 
                           help_text="Ex: GI-FI-N3")
    specialite = models.CharField(max_length=10, choices=SPECIALITES, verbose_name="Spécialité")
    formation = models.CharField(max_length=2, choices=FORMATIONS, verbose_name="Type de formation")
    niveau = models.CharField(max_length=2, choices=NIVEAUX, verbose_name="Niveau")
    
    # Horaires
    jour_semaine = models.CharField(max_length=10, choices=JOURS_SEMAINE, 
                                    blank=True, null=True, verbose_name="Jour principal")
    heure_debut = models.TimeField(blank=True, null=True, verbose_name="Heure de début")
    heure_fin = models.TimeField(blank=True, null=True, verbose_name="Heure de fin")
    
    # Informations complémentaires
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    salle_principale = models.ForeignKey('courses.Salle', on_delete=models.SET_NULL, 
                                        null=True, blank=True, 
                                        related_name='filieres_principales',
                                        verbose_name="Salle principale")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['specialite', 'formation', 'niveau']
        unique_together = ['specialite', 'formation', 'niveau']
    
    def __str__(self):
        return self.nom_complet()
    
    def nom_complet(self):
        """Retourne le nom complet de la filière"""
        return f"{self.get_specialite_display()} - {self.get_formation_display()} - {self.get_niveau_display()}"
    
    def nom_court(self):
        """Retourne un nom court"""
        return f"{self.specialite}-{self.formation}-{self.niveau}"
    
    def save(self, *args, **kwargs):
        """Générer automatiquement le code si vide"""
        if not self.code:
            self.code = self.nom_court()
        super().save(*args, **kwargs)
    
    def get_horaire(self):
        """Retourne l'horaire formaté"""
        if self.jour_semaine and self.heure_debut and self.heure_fin:
            return f"{self.get_jour_semaine_display()} {self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}"
        return "Non défini"


class HoraireSupplementaire(models.Model):
    """Horaires supplémentaires pour une filière (si plusieurs créneaux)"""
    
    JOURS_SEMAINE = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
        ('DIMANCHE', 'Dimanche'),
    ]
    
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, 
                                related_name='horaires_supplementaires',
                                verbose_name="Filière")
    jour_semaine = models.CharField(max_length=10, choices=JOURS_SEMAINE, verbose_name="Jour")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    salle = models.ForeignKey('courses.Salle', on_delete=models.SET_NULL, 
                             null=True, blank=True, 
                             related_name='horaires_supplementaires',
                             verbose_name="Salle")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    remarque = models.CharField(max_length=200, blank=True, null=True, 
                                verbose_name="Remarque")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Horaire supplémentaire"
        verbose_name_plural = "Horaires supplémentaires"
        ordering = ['filiere', 'jour_semaine', 'heure_debut']
    
    def __str__(self):
        return f"{self.filiere.code} - {self.get_jour_semaine_display()} {self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}"


class Etudiant(models.Model):
    """Informations sur les étudiants"""
    
    # Matricules
    matricule = models.CharField(max_length=20, unique=True, verbose_name="Matricule", 
                                 help_text="Matricule personnel de l'étudiant")
    matricule_departement = models.CharField(max_length=20, unique=True, blank=True, null=True,
                                            verbose_name="Matricule Département",
                                            help_text="Matricule généré automatiquement (ex: 25GITGRT300001)")
    
    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    filiere = models.ForeignKey('Filiere', on_delete=models.PROTECT, 
                                related_name='etudiants', 
                                verbose_name="Filière")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True, 
                                     verbose_name="Lieu de naissance")
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')], 
                           blank=True, null=True)
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    date_inscription = models.DateField(auto_now_add=True, verbose_name="Date d'inscription")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    photo = models.ImageField(upload_to='etudiants/photos/', blank=True, null=True, 
                             verbose_name="Photo")
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        if self.matricule_departement:
            return f"{self.matricule_departement} - {self.nom} {self.prenom}"
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
    
    def generer_matricule_departement(self):
        """
        Génère un matricule département automatique
        Format : AAGITSPECNXXXXX
        - AA = Année académique (2 chiffres)
        - GIT = Département (fixe)
        - SPEC = Spécialité (3 lettres)
        - N = Niveau (1 chiffre)
        - XXXXX = Numéro incrémental (5 chiffres)
        
        Exemple : 25GITGRT300001
        """
        # 1. Année académique (2 derniers chiffres)
        annee = str(datetime.now().year)[-2:]
        
        # 2. Département (fixe)
        departement = "GIT"
        
        # 3. Spécialité (prendre les 3 premières lettres)
        specialite = self.filiere.specialite[:3].upper()
        
        # 4. Niveau (extraire le chiffre de N1, N2, etc.)
        niveau = self.filiere.niveau[-1]  # N3 → 3
        
        # 5. Numéro incrémental
        # Chercher le dernier matricule avec ce pattern
        pattern_base = f"{annee}{departement}{specialite}{niveau}"
        
        # Récupérer tous les matricules qui commencent par ce pattern
        derniers_matricules = Etudiant.objects.filter(
            matricule_departement__startswith=pattern_base
        ).exclude(
            id=self.id  # Exclure l'étudiant actuel si on régénère
        ).values_list('matricule_departement', flat=True)
        
        # Trouver le numéro le plus élevé
        max_numero = 0
        for mat in derniers_matricules:
            try:
                # Extraire les 5 derniers chiffres
                numero = int(mat[-5:])
                if numero > max_numero:
                    max_numero = numero
            except (ValueError, IndexError):
                continue
        
        # Incrémenter et formater sur 5 chiffres
        nouveau_numero = max_numero + 1
        numero_formate = str(nouveau_numero).zfill(5)
        
        # 6. Assembler le matricule complet
        matricule_complet = f"{pattern_base}{numero_formate}"
        
        return matricule_complet
    
    def save(self, *args, **kwargs):
        """
        Générer automatiquement le matricule département si absent
        """
        # Générer le matricule département si vide
        if not self.matricule_departement and self.filiere:
            self.matricule_departement = self.generer_matricule_departement()
        
        super().save(*args, **kwargs)