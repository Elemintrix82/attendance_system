from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Filiere, HoraireSupplementaire, Etudiant


# ============================================
# RESOURCES POUR IMPORT/EXPORT
# ============================================

class FiliereResource(resources.ModelResource):
    class Meta:
        model = Filiere
        fields = ('id', 'code', 'specialite', 'formation', 'niveau', 
                 'jour_semaine', 'heure_debut', 'heure_fin', 'description')
        export_order = ('id', 'code', 'specialite', 'formation', 'niveau', 
                       'jour_semaine', 'heure_debut', 'heure_fin')


class EtudiantResource(resources.ModelResource):
    filiere = resources.Field(
        column_name='filiere',
        attribute='filiere',
        widget=resources.widgets.ForeignKeyWidget(Filiere, 'code')
    )
    
    class Meta:
        model = Etudiant
        fields = ('id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 
                 'filiere', 'date_naissance', 'lieu_naissance', 
                 'sexe', 'adresse', 'actif')
        export_order = ('matricule', 'nom', 'prenom', 'email', 'telephone', 
                       'filiere', 'sexe', 'date_naissance', 
                       'lieu_naissance', 'adresse', 'actif')
        import_id_fields = ['matricule']
        skip_unchanged = True


# ============================================
# INLINE ADMINS
# ============================================

class HoraireSupplementaireInline(admin.TabularInline):
    """Inline pour gérer les horaires supplémentaires"""
    model = HoraireSupplementaire
    extra = 1
    fields = ('jour_semaine', 'heure_debut', 'heure_fin', 'salle', 'remarque', 'actif')
    autocomplete_fields = ['salle']


# ============================================
# MODEL ADMINS
# ============================================

@admin.register(Filiere)
class FiliereAdmin(ImportExportModelAdmin):
    resource_class = FiliereResource
    list_display = ('code', 'specialite_display', 'formation_display', 
                   'niveau_display', 'horaire_principal', 'nombre_etudiants', 
                   'nombre_cours', 'actif')
    search_fields = ('code', 'specialite', 'formation', 'niveau')
    list_filter = ('specialite', 'formation', 'niveau', 'actif', 'jour_semaine')
    ordering = ('specialite', 'formation', 'niveau')
    inlines = [HoraireSupplementaireInline]
    autocomplete_fields = ['salle_principale']
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'specialite', 'formation', 'niveau')
        }),
        ('Horaire principal', {
            'fields': ('jour_semaine', 'heure_debut', 'heure_fin', 'salle_principale')
        }),
        ('Informations complémentaires', {
            'fields': ('description', 'actif')
        }),
    )
    
    def specialite_display(self, obj):
        return obj.get_specialite_display()
    specialite_display.short_description = "Spécialité"
    
    def formation_display(self, obj):
        return obj.get_formation_display()
    formation_display.short_description = "Formation"
    
    def niveau_display(self, obj):
        return obj.get_niveau_display()
    niveau_display.short_description = "Niveau"
    
    def horaire_principal(self, obj):
        return obj.get_horaire()
    horaire_principal.short_description = "Horaire principal"
    
    def nombre_etudiants(self, obj):
        count = obj.etudiants.filter(actif=True).count()
        return f'{count} étudiant(s)'
    nombre_etudiants.short_description = "Étudiants actifs"
    
    def nombre_cours(self, obj):
        count = obj.cours.filter(actif=True).count()
        return f'{count} cours'
    nombre_cours.short_description = "Cours"


@admin.register(HoraireSupplementaire)
class HoraireSupplementaireAdmin(admin.ModelAdmin):
    list_display = ('filiere', 'jour_semaine', 'heure_debut', 'heure_fin', 'salle', 'actif')
    search_fields = ('filiere__code', 'jour_semaine')
    list_filter = ('filiere__specialite', 'jour_semaine', 'actif')
    ordering = ('filiere', 'jour_semaine', 'heure_debut')
    autocomplete_fields = ['filiere', 'salle']
    
    fieldsets = (
        ('Filière', {
            'fields': ('filiere',)
        }),
        ('Horaire', {
            'fields': ('jour_semaine', 'heure_debut', 'heure_fin', 'salle')
        }),
        ('Détails', {
            'fields': ('remarque', 'actif')
        }),
    )


@admin.register(Etudiant)
class EtudiantAdmin(ImportExportModelAdmin):
    resource_class = EtudiantResource
    list_display = ('matricule', 'matricule_departement', 'nom', 'prenom', 'filiere_complete', 
                   'email', 'actif', 'taux_presence_display')
    search_fields = ('matricule', 'nom', 'prenom', 'email')
    list_filter = ('filiere__specialite', 'filiere__formation', 'filiere__niveau', 
                  'sexe', 'actif', 'date_inscription')
    ordering = ('nom', 'prenom')
    readonly_fields = ('date_inscription',)
    autocomplete_fields = ['filiere']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 
                      'lieu_naissance', 'photo')
        }),
        ('Informations académiques', {
            'fields': ('filiere', 'date_inscription', 'actif')
        }),
        ('Contact', {
            'fields': ('email', 'telephone', 'adresse')
        }),
    )
    
    def filiere_complete(self, obj):
        return obj.filiere.nom_complet()
    filiere_complete.short_description = "Filière"
    
    def taux_presence_display(self, obj):
        taux = obj.get_taux_presence()
        if taux >= 75:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return f'<span style="color: {color}; font-weight: bold;">{taux}%</span>'
    taux_presence_display.short_description = "Taux de présence"
    taux_presence_display.allow_tags = True
    
    actions = ['activer_etudiants', 'desactiver_etudiants']
    
    def activer_etudiants(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'✅ {updated} étudiant(s) activé(s).')
    activer_etudiants.short_description = "✅ Activer les étudiants sélectionnés"
    
    def desactiver_etudiants(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'⛔ {updated} étudiant(s) désactivé(s).')
    desactiver_etudiants.short_description = "⛔ Désactiver les étudiants sélectionnés"