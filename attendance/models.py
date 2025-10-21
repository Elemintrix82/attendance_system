from django.db import models
from django.contrib.auth.models import User
from students.models import Etudiant
from courses.models import SeanceCours


class Presence(models.Model):
    """Présence des étudiants aux séances"""
    STATUTS = [
        ('P', 'Présent'),
        ('A', 'Absent'),
        ('R', 'Retard'),
        ('J', 'Justifié'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, 
                                related_name='presences', 
                                verbose_name="Étudiant")
    seance = models.ForeignKey(SeanceCours, on_delete=models.CASCADE, 
                              related_name='presences',
                              verbose_name="Séance")
    statut = models.CharField(max_length=1, choices=STATUTS, default='A', verbose_name="Statut")
    remarque = models.TextField(blank=True, null=True, verbose_name="Remarque")
    justification = models.FileField(upload_to='justificatifs/', 
                                     blank=True, null=True,
                                     verbose_name="Justificatif")
    heure_arrivee = models.TimeField(blank=True, null=True, verbose_name="Heure d'arrivée")
    date_saisie = models.DateTimeField(auto_now_add=True, verbose_name="Date de saisie")
    date_modification = models.DateTimeField(auto_now=True)
    saisi_par = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, blank=True,
                                  verbose_name="Saisi par")
    
    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        ordering = ['-seance__date', 'etudiant__nom']
        unique_together = ['etudiant', 'seance']
    
    def __str__(self):
        return f"{self.etudiant.nom_complet()} - {self.seance} ({self.get_statut_display()})"
    
    def est_present(self):
        """Vérifie si l'étudiant est considéré comme présent"""
        return self.statut in ['P', 'R', 'J']
    
    def est_absent_injustifie(self):
        """Vérifie si l'absence est injustifiée"""
        return self.statut == 'A'


class Justificatif(models.Model):
    """Justificatifs d'absence des étudiants"""
    TYPE_JUSTIFICATIF = [
        ('MEDICAL', 'Certificat médical'),
        ('FAMILLE', 'Raison familiale'),
        ('ADMIN', 'Raison administrative'),
        ('AUTRE', 'Autre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, 
                                related_name='justificatifs',
                                verbose_name="Étudiant")
    type_justificatif = models.CharField(max_length=20, choices=TYPE_JUSTIFICATIF, 
                                        verbose_name="Type de justificatif")
    motif = models.TextField(verbose_name="Motif")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    fichier = models.FileField(upload_to='justificatifs/', verbose_name="Fichier")
    valide = models.BooleanField(default=False, verbose_name="Validé")
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, blank=True,
                                   related_name='justificatifs_valides',
                                   verbose_name="Validé par")
    date_validation = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")
    remarque_validation = models.TextField(blank=True, null=True, verbose_name="Remarque de validation")
    date_soumission = models.DateTimeField(auto_now_add=True, verbose_name="Date de soumission")
    
    class Meta:
        verbose_name = "Justificatif"
        verbose_name_plural = "Justificatifs"
        ordering = ['-date_soumission']
    
    def __str__(self):
        return f"{self.etudiant.nom_complet()} - {self.get_type_justificatif_display()} ({self.date_debut} au {self.date_fin})"
    
    def nombre_jours(self):
        """Calcule le nombre de jours couverts par le justificatif"""
        delta = self.date_fin - self.date_debut
        return delta.days + 1