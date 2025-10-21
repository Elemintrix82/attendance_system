from django.db import models
from django.contrib.auth.models import User
from students.models import Etudiant, Filiere, Niveau
from courses.models import Cours


class RapportPresence(models.Model):
    """Rapports de présence générés"""
    TYPE_RAPPORT = [
        ('ETUDIANT', 'Par étudiant'),
        ('COURS', 'Par cours'),
        ('FILIERE', 'Par filière'),
        ('NIVEAU', 'Par niveau'),
        ('GLOBAL', 'Global'),
    ]
    
    FORMAT_RAPPORT = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    type_rapport = models.CharField(max_length=20, choices=TYPE_RAPPORT, 
                                   verbose_name="Type de rapport")
    format_fichier = models.CharField(max_length=10, choices=FORMAT_RAPPORT, 
                                     default='PDF',
                                     verbose_name="Format")
    
    # Filtres utilisés
    etudiant = models.ForeignKey(Etudiant, on_delete=models.SET_NULL, 
                                null=True, blank=True,
                                verbose_name="Étudiant")
    cours = models.ForeignKey(Cours, on_delete=models.SET_NULL, 
                             null=True, blank=True,
                             verbose_name="Cours")
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               verbose_name="Filière")
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, 
                              null=True, blank=True,
                              verbose_name="Niveau")
    
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date de début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date de fin")
    
    # Fichier généré
    fichier = models.FileField(upload_to='rapports/', 
                              blank=True, null=True,
                              verbose_name="Fichier")
    
    # Métadonnées
    genere_par = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True,
                                  verbose_name="Généré par")
    date_generation = models.DateTimeField(auto_now_add=True, 
                                          verbose_name="Date de génération")
    nombre_pages = models.IntegerField(default=1, verbose_name="Nombre de pages")
    taille_fichier = models.IntegerField(default=0, 
                                        help_text="Taille en octets",
                                        verbose_name="Taille du fichier")
    
    class Meta:
        verbose_name = "Rapport de présence"
        verbose_name_plural = "Rapports de présence"
        ordering = ['-date_generation']
    
    def __str__(self):
        return f"{self.titre} - {self.date_generation.strftime('%d/%m/%Y %H:%M')}"


class StatistiqueCache(models.Model):
    """Cache des statistiques calculées pour améliorer les performances"""
    cle = models.CharField(max_length=200, unique=True, 
                          verbose_name="Clé")
    valeur = models.JSONField(verbose_name="Valeur")
    date_calcul = models.DateTimeField(auto_now=True, 
                                      verbose_name="Date de calcul")
    date_expiration = models.DateTimeField(verbose_name="Date d'expiration")
    
    class Meta:
        verbose_name = "Statistique en cache"
        verbose_name_plural = "Statistiques en cache"
        ordering = ['-date_calcul']
    
    def __str__(self):
        return self.cle
    
    def est_expire(self):
        """Vérifie si le cache est expiré"""
        from django.utils import timezone
        return timezone.now() > self.date_expiration