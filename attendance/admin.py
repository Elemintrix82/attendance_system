from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Presence, Justificatif
from students.models import Etudiant
from courses.models import SeanceCours


# ============================================
# RESOURCES POUR IMPORT/EXPORT
# ============================================

class PresenceResource(resources.ModelResource):
    """Resource pour l'import/export des présences"""
    etudiant = resources.Field(
        column_name='matricule_etudiant',
        attribute='etudiant',
        widget=resources.widgets.ForeignKeyWidget(Etudiant, 'matricule')
    )
    seance = resources.Field(
        column_name='seance_id',
        attribute='seance',
        widget=resources.widgets.ForeignKeyWidget(SeanceCours, 'id')
    )
    
    class Meta:
        model = Presence
        fields = ('id', 'etudiant', 'seance', 'statut', 'remarque', 
                 'heure_arrivee', 'date_saisie')
        export_order = ('etudiant', 'seance', 'statut', 'heure_arrivee', 
                       'remarque', 'date_saisie')
        import_id_fields = ['etudiant', 'seance']
        skip_unchanged = True


class JustificatifResource(resources.ModelResource):
    """Resource pour l'import/export des justificatifs"""
    etudiant = resources.Field(
        column_name='matricule_etudiant',
        attribute='etudiant',
        widget=resources.widgets.ForeignKeyWidget(Etudiant, 'matricule')
    )
    
    class Meta:
        model = Justificatif
        fields = ('id', 'etudiant', 'type_justificatif', 'motif', 
                 'date_debut', 'date_fin', 'valide', 'date_soumission')
        export_order = ('etudiant', 'type_justificatif', 'motif', 
                       'date_debut', 'date_fin', 'valide', 'date_soumission')


# ============================================
# ADMIN POUR PRESENCE
# ============================================

@admin.register(Presence)
class PresenceAdmin(ImportExportModelAdmin):
    resource_class = PresenceResource
    list_display = ('etudiant', 'seance', 'statut_display', 'heure_arrivee', 
                   'remarque_courte', 'date_saisie', 'saisi_par')
    search_fields = ('etudiant__matricule', 'etudiant__nom', 'etudiant__prenom', 
                    'seance__cours__code', 'seance__cours__intitule')
    list_filter = ('statut', 'seance__date', 'seance__cours__filiere', 
                   'seance__type_seance')
    ordering = ('-seance__date', 'etudiant__nom')
    readonly_fields = ('date_saisie', 'date_modification')
    date_hierarchy = 'seance__date'
    
    fieldsets = (
        ('Étudiant et séance', {
            'fields': ('etudiant', 'seance')
        }),
        ('Présence', {
            'fields': ('statut', 'heure_arrivee', 'remarque')
        }),
        ('Justificatif', {
            'fields': ('justification',)
        }),
        ('Métadonnées', {
            'fields': ('saisi_par', 'date_saisie', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def statut_display(self, obj):
        colors = {
            'P': 'green',
            'A': 'red',
            'R': 'orange',
            'J': 'blue',
        }
        color = colors.get(obj.statut, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.get_statut_display()}</span>'
    statut_display.short_description = "Statut"
    statut_display.allow_tags = True
    
    def remarque_courte(self, obj):
        if obj.remarque:
            return obj.remarque[:50] + '...' if len(obj.remarque) > 50 else obj.remarque
        return '-'
    remarque_courte.short_description = "Remarque"
    
    actions = ['marquer_present', 'marquer_absent', 'marquer_retard']
    
    def marquer_present(self, request, queryset):
        updated = queryset.update(statut='P')
        self.message_user(request, f'{updated} présence(s) marquée(s) comme Présent.')
    marquer_present.short_description = "Marquer comme Présent"
    
    def marquer_absent(self, request, queryset):
        updated = queryset.update(statut='A')
        self.message_user(request, f'{updated} présence(s) marquée(s) comme Absent.')
    marquer_absent.short_description = "Marquer comme Absent"
    
    def marquer_retard(self, request, queryset):
        updated = queryset.update(statut='R')
        self.message_user(request, f'{updated} présence(s) marquée(s) comme Retard.')
    marquer_retard.short_description = "Marquer comme Retard"
    
    def save_model(self, request, obj, form, change):
        if not obj.saisi_par:
            obj.saisi_par = request.user
        super().save_model(request, obj, form, change)


# ============================================
# ADMIN POUR JUSTIFICATIF
# ============================================

@admin.register(Justificatif)
class JustificatifAdmin(ImportExportModelAdmin):
    resource_class = JustificatifResource
    list_display = ('etudiant', 'type_justificatif', 'date_debut', 'date_fin', 
                   'nombre_jours_display', 'valide_display', 'date_soumission')
    search_fields = ('etudiant__matricule', 'etudiant__nom', 'etudiant__prenom', 'motif')
    list_filter = ('type_justificatif', 'valide', 'date_debut', 'date_fin', 'date_soumission')
    ordering = ('-date_soumission',)
    readonly_fields = ('date_soumission', 'date_validation', 'date_modification')
    date_hierarchy = 'date_soumission'
    
    fieldsets = (
        ('Étudiant', {
            'fields': ('etudiant',)
        }),
        ('Justificatif', {
            'fields': ('type_justificatif', 'motif', 'date_debut', 'date_fin', 'fichier')
        }),
        ('Validation', {
            'fields': ('valide', 'valide_par', 'date_validation', 'remarque_validation')
        }),
        ('Métadonnées', {
            'fields': ('date_soumission', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def valide_display(self, obj):
        if obj.valide:
            return '<span style="color: green; font-weight: bold;">✓ Validé</span>'
        return '<span style="color: orange;">⏳ En attente</span>'
    valide_display.short_description = "Validation"
    valide_display.allow_tags = True
    
    def nombre_jours_display(self, obj):
        return f"{obj.nombre_jours()} jour(s)"
    nombre_jours_display.short_description = "Durée"
    
    actions = ['valider_justificatifs', 'refuser_justificatifs']
    
    def valider_justificatifs(self, request, queryset):
        from django.utils import timezone
        count = 0
        for justificatif in queryset:
            justificatif.valide = True
            justificatif.valide_par = request.user
            justificatif.date_validation = timezone.now()
            justificatif.save()
            count += 1
        self.message_user(request, f'{count} justificatif(s) validé(s).')
    valider_justificatifs.short_description = "Valider les justificatifs sélectionnés"
    
    def refuser_justificatifs(self, request, queryset):
        updated = queryset.update(valide=False, valide_par=None, date_validation=None)
        self.message_user(request, f'{updated} justificatif(s) refusé(s).')
    refuser_justificatifs.short_description = "Refuser les justificatifs sélectionnés"
    
    def save_model(self, request, obj, form, change):
        # Si on valide via l'admin et qu'il n'y a pas de validateur
        if obj.valide and not obj.valide_par:
            from django.utils import timezone
            obj.valide_par = request.user
            obj.date_validation = timezone.now()
        super().save_model(request, obj, form, change)