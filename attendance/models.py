from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from students.models import Etudiant
from courses.models import SeanceCours
from datetime import datetime


class Presence(models.Model):
    """Enregistrement de présence pour une séance"""
    
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
    statut = models.CharField(max_length=1, choices=STATUTS, default='A',
                             verbose_name="Statut")
    heure_arrivee = models.TimeField(blank=True, null=True,
                                     verbose_name="Heure d'arrivée")
    remarque = models.TextField(blank=True, null=True,
                                verbose_name="Remarque")
    
    # 🆕 JUSTIFICATION RAPIDE (pour usage immédiat)
    justification = models.FileField(upload_to='presences/justificatifs/',
                                     blank=True, null=True,
                                     validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
                                     verbose_name="Justificatif rapide",
                                     help_text="Pour justification immédiate lors de la séance")
    
    # 🆕 LIEN VERS JUSTIFICATIF FORMEL (validation administrative)
    justificatif_formel = models.ForeignKey('Justificatif', on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='presences_couvertes',
                                           verbose_name="Justificatif formel",
                                           help_text="Justificatif validé par l'administration")
    
    saisi_par = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='presences_saisies',
                                  verbose_name="Saisi par")
    date_saisie = models.DateTimeField(auto_now_add=True,
                                       verbose_name="Date de saisie")
    date_modification = models.DateTimeField(auto_now=True,
                                            verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        ordering = ['-seance__date', 'etudiant__nom']
        unique_together = ['etudiant', 'seance']
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.seance.cours.code} ({self.get_statut_display()})"
    
    def est_present(self):
        """Vérifie si l'étudiant est considéré comme présent"""
        return self.statut in ['P', 'R', 'J']
    
    def est_absent(self):
        """Vérifie si l'étudiant est absent"""
        return self.statut == 'A'
    
    # 🆕 NOUVELLES MÉTHODES
    def a_justification(self):
        """Vérifie s'il y a une justification (rapide OU formelle)"""
        return bool(self.justification or self.justificatif_formel)
    
    def justification_validee(self):
        """Vérifie si la justification est validée administrativement"""
        return self.justificatif_formel and self.justificatif_formel.valide
    
    def type_justification(self):
        """Retourne le type de justification"""
        if self.justificatif_formel and self.justificatif_formel.valide:
            return "✅ Validé (Admin)"
        elif self.justificatif_formel:
            return "⏳ En attente (Admin)"
        elif self.justification:
            return "📄 Justificatif fourni"
        elif self.statut == 'J':
            return "⚠️ Marqué justifié (pas de document)"
        return "❌ Non justifié"


class Justificatif(models.Model):
    """Justificatifs d'absence des étudiants - Processus administratif formel"""
    
    TYPES_JUSTIFICATIF = [
        ('MEDICAL', 'Certificat Médical'),
        ('FAMILLE', 'Raison Familiale'),
        ('ADMIN', 'Démarche Administrative'),
        ('STAGE', 'Stage/Formation'),
        ('AUTRE', 'Autre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE,
                                 related_name='justificatifs',
                                 verbose_name="Étudiant")
    type_justificatif = models.CharField(max_length=20, choices=TYPES_JUSTIFICATIF,
                                        verbose_name="Type de justificatif")
    motif = models.TextField(verbose_name="Motif de l'absence")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(blank=True, null=True,
                                verbose_name="Date de fin")
    fichier = models.FileField(upload_to='justificatifs/',
                               blank=True, null=True,
                               validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
                               verbose_name="Document justificatif")
    
    # Validation
    valide = models.BooleanField(default=False,
                                 verbose_name="Validé")
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='justificatifs_valides',
                                   verbose_name="Validé par")
    date_validation = models.DateTimeField(blank=True, null=True,
                                          verbose_name="Date de validation")
    remarque_validation = models.TextField(blank=True, null=True,
                                          verbose_name="Remarque de validation")
    
    # Métadonnées
    date_soumission = models.DateTimeField(auto_now_add=True,
                                          verbose_name="Date de soumission")
    date_modification = models.DateTimeField(auto_now=True,
                                            verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Justificatif"
        verbose_name_plural = "Justificatifs"
        ordering = ['-date_soumission']
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.get_type_justificatif_display()} ({self.date_debut})"
    
    def nombre_jours(self):
        """Calcule le nombre de jours d'absence"""
        if self.date_fin:
            delta = self.date_fin - self.date_debut
            return delta.days + 1
        return 1
    
    def est_valide(self):
        """Vérifie si le justificatif est validé"""
        return self.valide
    
    def peut_etre_valide(self):
        """Vérifie si le justificatif peut encore être validé"""
        return not self.valide
    
    # 🆕 NOUVELLES MÉTHODES
    def presences_concernees(self):
        """Retourne toutes les présences couvertes par ce justificatif"""
        from django.db.models import Q
        
        # Chercher toutes les présences de cet étudiant dans la période
        query = Q(etudiant=self.etudiant, seance__date__gte=self.date_debut)
        
        if self.date_fin:
            query &= Q(seance__date__lte=self.date_fin)
        else:
            query &= Q(seance__date=self.date_debut)
        
        return Presence.objects.filter(query)
    
    def appliquer_aux_presences(self):
        """Applique ce justificatif à toutes les présences concernées"""
        presences = self.presences_concernees()
        count = 0
        
        for presence in presences:
            if presence.statut == 'A':  # Seulement les absences
                presence.statut = 'J'
                presence.justificatif_formel = self
                presence.save()
                count += 1
        
        return count
    
    def retirer_des_presences(self):
        """Retire ce justificatif des présences (en cas de refus)"""
        presences = Presence.objects.filter(justificatif_formel=self)
        count = 0
        
        for presence in presences:
            presence.statut = 'A'  # Remettre en absent
            presence.justificatif_formel = None
            presence.save()
            count += 1
        
        return count