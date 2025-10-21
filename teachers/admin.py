from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Enseignant


# Resource pour l'import/export Excel
class EnseignantResource(resources.ModelResource):
    class Meta:
        model = Enseignant
        fields = ('id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 
                 'specialite', 'grade', 'date_naissance', 'sexe', 'adresse', 
                 'date_embauche', 'actif')
        export_order = ('matricule', 'nom', 'prenom', 'email', 'telephone', 
                       'specialite', 'grade', 'sexe', 'date_naissance', 
                       'date_embauche', 'actif')
        import_id_fields = ['matricule']
        skip_unchanged = True
    
    def before_import_row(self, row, **kwargs):
        """Créer automatiquement un User pour chaque enseignant importé"""
        matricule = row.get('matricule')
        email = row.get('email')
        nom = row.get('nom', '')
        prenom = row.get('prenom', '')
        
        # Vérifier si le user existe déjà
        if not User.objects.filter(username=matricule).exists():
            # Créer le user
            user = User.objects.create_user(
                username=matricule,
                email=email,
                first_name=prenom,
                last_name=nom,
                password=matricule  # Mot de passe par défaut = matricule
            )
            user.save()


# Admin pour Enseignant
@admin.register(Enseignant)
class EnseignantAdmin(ImportExportModelAdmin):
    resource_class = EnseignantResource
    list_display = ('matricule', 'nom', 'prenom', 'email', 'grade', 
                   'specialite', 'nombre_cours', 'actif')
    search_fields = ('matricule', 'nom', 'prenom', 'email', 'specialite')
    list_filter = ('grade', 'actif', 'date_embauche', 'specialite')
    ordering = ('nom', 'prenom')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Compte utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 'photo')
        }),
        ('Informations professionnelles', {
            'fields': ('email', 'telephone', 'specialite', 'grade', 'date_embauche', 'actif')
        }),
        ('Adresse', {
            'fields': ('adresse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_cours(self, obj):
        return obj.get_nombre_cours()
    nombre_cours.short_description = "Nb cours"
    
    actions = ['activer_enseignants', 'desactiver_enseignants', 'reinitialiser_mot_de_passe']
    
    def activer_enseignants(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} enseignant(s) activé(s).')
    activer_enseignants.short_description = "Activer les enseignants sélectionnés"
    
    def desactiver_enseignants(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} enseignant(s) désactivé(s).')
    desactiver_enseignants.short_description = "Désactiver les enseignants sélectionnés"
    
    def reinitialiser_mot_de_passe(self, request, queryset):
        count = 0
        for enseignant in queryset:
            if enseignant.user:
                enseignant.user.set_password(enseignant.matricule)
                enseignant.user.save()
                count += 1
        self.message_user(request, f'Mot de passe réinitialisé pour {count} enseignant(s).')
    reinitialiser_mot_de_passe.short_description = "Réinitialiser mot de passe (= matricule)"