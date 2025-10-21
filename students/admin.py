from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Filiere, Niveau, Etudiant


# Resources pour l'import/export Excel
class FiliereResource(resources.ModelResource):
    class Meta:
        model = Filiere
        fields = ('id', 'code', 'nom', 'description')
        export_order = ('id', 'code', 'nom', 'description')


class NiveauResource(resources.ModelResource):
    class Meta:
        model = Niveau
        fields = ('id', 'nom', 'cycle', 'annee')
        export_order = ('id', 'nom', 'cycle', 'annee')


class EtudiantResource(resources.ModelResource):
    filiere = resources.Field(
        column_name='filiere',
        attribute='filiere',
        widget=resources.widgets.ForeignKeyWidget(Filiere, 'code')
    )
    niveau = resources.Field(
        column_name='niveau',
        attribute='niveau',
        widget=resources.widgets.ForeignKeyWidget(Niveau, 'nom')
    )
    
    class Meta:
        model = Etudiant
        fields = ('id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 
                 'filiere', 'niveau', 'date_naissance', 'lieu_naissance', 
                 'sexe', 'adresse', 'actif')
        export_order = ('matricule', 'nom', 'prenom', 'email', 'telephone', 
                       'filiere', 'niveau', 'sexe', 'date_naissance', 
                       'lieu_naissance', 'adresse', 'actif')
        import_id_fields = ['matricule']
        skip_unchanged = True


# Admin pour Filiere
@admin.register(Filiere)
class FiliereAdmin(ImportExportModelAdmin):
    resource_class = FiliereResource
    list_display = ('code', 'nom', 'nombre_etudiants', 'date_creation')
    search_fields = ('code', 'nom')
    list_filter = ('date_creation',)
    ordering = ('code',)
    
    def nombre_etudiants(self, obj):
        return obj.etudiants.filter(actif=True).count()
    nombre_etudiants.short_description = "Nb étudiants actifs"


# Admin pour Niveau
@admin.register(Niveau)
class NiveauAdmin(ImportExportModelAdmin):
    resource_class = NiveauResource
    list_display = ('nom', 'cycle', 'annee', 'nombre_etudiants')
    search_fields = ('nom',)
    list_filter = ('cycle', 'annee')
    ordering = ('cycle', 'annee')
    
    def nombre_etudiants(self, obj):
        return obj.etudiants.filter(actif=True).count()
    nombre_etudiants.short_description = "Nb étudiants actifs"


# Admin pour Etudiant
@admin.register(Etudiant)
class EtudiantAdmin(ImportExportModelAdmin):
    resource_class = EtudiantResource
    list_display = ('matricule', 'nom', 'prenom', 'filiere', 'niveau', 
                   'email', 'actif', 'taux_presence')
    search_fields = ('matricule', 'nom', 'prenom', 'email')
    list_filter = ('filiere', 'niveau', 'sexe', 'actif', 'date_inscription')
    ordering = ('nom', 'prenom')
    readonly_fields = ('date_inscription',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 
                      'lieu_naissance', 'photo')
        }),
        ('Informations académiques', {
            'fields': ('filiere', 'niveau', 'date_inscription', 'actif')
        }),
        ('Contact', {
            'fields': ('email', 'telephone', 'adresse')
        }),
    )
    
    def taux_presence(self, obj):
        taux = obj.get_taux_presence()
        if taux >= 75:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return f'<span style="color: {color}; font-weight: bold;">{taux}%</span>'
    taux_presence.short_description = "Taux de présence"
    taux_presence.allow_tags = True
    
    actions = ['activer_etudiants', 'desactiver_etudiants']
    
    def activer_etudiants(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} étudiant(s) activé(s).')
    activer_etudiants.short_description = "Activer les étudiants sélectionnés"
    
    def desactiver_etudiants(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} étudiant(s) désactivé(s).')
    desactiver_etudiants.short_description = "Désactiver les étudiants sélectionnés"