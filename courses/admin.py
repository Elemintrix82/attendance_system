from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Salle, Cours, SeanceCours
from students.models import Filiere, Niveau
from teachers.models import Enseignant


# Resources pour l'import/export Excel
class SalleResource(resources.ModelResource):
    class Meta:
        model = Salle
        fields = ('id', 'nom', 'type_salle', 'capacite', 'batiment', 
                 'etage', 'equipements', 'disponible')
        export_order = ('nom', 'type_salle', 'capacite', 'batiment', 
                       'etage', 'equipements', 'disponible')
        import_id_fields = ['nom']
        skip_unchanged = True


class CoursResource(resources.ModelResource):
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
    enseignant = resources.Field(
        column_name='enseignant_matricule',
        attribute='enseignant',
        widget=resources.widgets.ForeignKeyWidget(Enseignant, 'matricule')
    )
    salle = resources.Field(
        column_name='salle',
        attribute='salle',
        widget=resources.widgets.ForeignKeyWidget(Salle, 'nom')
    )
    
    class Meta:
        model = Cours
        fields = ('id', 'code', 'intitule', 'description', 'filiere', 'niveau', 
                 'enseignant', 'salle', 'semestre', 'annee_academique', 
                 'jour_semaine', 'heure_debut', 'heure_fin', 'credits', 
                 'coefficient', 'volume_horaire_cm', 'volume_horaire_td', 
                 'volume_horaire_tp', 'actif')
        export_order = ('code', 'intitule', 'filiere', 'niveau', 'enseignant', 
                       'semestre', 'annee_academique', 'jour_semaine', 
                       'heure_debut', 'heure_fin', 'salle', 'credits', 
                       'coefficient', 'actif')
        import_id_fields = ['code', 'annee_academique']
        skip_unchanged = True


class SeanceCoursResource(resources.ModelResource):
    cours = resources.Field(
        column_name='cours_code',
        attribute='cours',
        widget=resources.widgets.ForeignKeyWidget(Cours, 'code')
    )
    salle = resources.Field(
        column_name='salle',
        attribute='salle',
        widget=resources.widgets.ForeignKeyWidget(Salle, 'nom')
    )
    
    class Meta:
        model = SeanceCours
        fields = ('id', 'cours', 'date', 'heure_debut', 'heure_fin', 
                 'salle', 'type_seance', 'contenu', 'presente')
        export_order = ('cours', 'date', 'heure_debut', 'heure_fin', 
                       'salle', 'type_seance', 'presente')
        import_id_fields = ['cours', 'date', 'heure_debut']
        skip_unchanged = True


# Admin pour Salle
@admin.register(Salle)
class SalleAdmin(ImportExportModelAdmin):
    resource_class = SalleResource
    list_display = ('nom', 'type_salle', 'capacite', 'batiment', 'etage', 
                   'disponible', 'nombre_cours')
    search_fields = ('nom', 'batiment')
    list_filter = ('type_salle', 'disponible', 'batiment')
    ordering = ('batiment', 'nom')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'type_salle', 'capacite', 'disponible')
        }),
        ('Localisation', {
            'fields': ('batiment', 'etage')
        }),
        ('Équipements', {
            'fields': ('equipements',)
        }),
    )
    
    def nombre_cours(self, obj):
        return obj.cours.filter(actif=True).count()
    nombre_cours.short_description = "Nb cours"
    
    actions = ['rendre_disponible', 'rendre_indisponible']
    
    def rendre_disponible(self, request, queryset):
        updated = queryset.update(disponible=True)
        self.message_user(request, f'{updated} salle(s) rendue(s) disponible(s).')
    rendre_disponible.short_description = "Rendre disponible"
    
    def rendre_indisponible(self, request, queryset):
        updated = queryset.update(disponible=False)
        self.message_user(request, f'{updated} salle(s) rendue(s) indisponible(s).')
    rendre_indisponible.short_description = "Rendre indisponible"


# Admin pour Cours
@admin.register(Cours)
class CoursAdmin(ImportExportModelAdmin):
    resource_class = CoursResource
    list_display = ('code', 'intitule', 'filiere', 'niveau', 'enseignant', 
                   'semestre', 'annee_academique', 'credits', 'actif', 'nb_seances')
    search_fields = ('code', 'intitule', 'enseignant__nom', 'enseignant__prenom')
    list_filter = ('filiere', 'niveau', 'semestre', 'annee_academique', 
                  'actif', 'jour_semaine')
    ordering = ('code',)
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('code', 'intitule', 'description', 'actif')
        }),
        ('Affectation académique', {
            'fields': ('filiere', 'niveau', 'semestre', 'annee_academique')
        }),
        ('Enseignant et salle', {
            'fields': ('enseignant', 'salle')
        }),
        ('Horaires', {
            'fields': ('jour_semaine', 'heure_debut', 'heure_fin')
        }),
        ('Crédits et volumes', {
            'fields': ('credits', 'coefficient', 'volume_horaire_cm', 
                      'volume_horaire_td', 'volume_horaire_tp')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def nb_seances(self, obj):
        return obj.get_nombre_seances()
    nb_seances.short_description = "Nb séances"
    
    actions = ['activer_cours', 'desactiver_cours']
    
    def activer_cours(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} cours activé(s).')
    activer_cours.short_description = "Activer les cours sélectionnés"
    
    def desactiver_cours(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} cours désactivé(s).')
    desactiver_cours.short_description = "Désactiver les cours sélectionnés"


# Admin pour SeanceCours
@admin.register(SeanceCours)
class SeanceCoursAdmin(ImportExportModelAdmin):
    resource_class = SeanceCoursResource
    list_display = ('cours', 'date', 'heure_debut', 'heure_fin', 'type_seance', 
                   'salle', 'presente', 'taux_presence_display')
    search_fields = ('cours__code', 'cours__intitule')
    list_filter = ('type_seance', 'presente', 'date', 'cours__filiere', 'cours__niveau')
    ordering = ('-date', '-heure_debut')
    readonly_fields = ('date_creation', 'date_modification')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Cours et horaires', {
            'fields': ('cours', 'date', 'heure_debut', 'heure_fin', 'salle')
        }),
        ('Détails de la séance', {
            'fields': ('type_seance', 'contenu', 'presente')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def taux_presence_display(self, obj):
        if not obj.presente:
            return '-'
        taux = obj.get_taux_presence()
        if taux >= 75:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return f'<span style="color: {color}; font-weight: bold;">{taux}%</span>'
    taux_presence_display.short_description = "Taux présence"
    taux_presence_display.allow_tags = True
    
    actions = ['marquer_presente_faite']
    
    def marquer_presente_faite(self, request, queryset):
        updated = queryset.update(presente=True)
        self.message_user(request, f'Présence marquée comme faite pour {updated} séance(s).')
    marquer_presente_faite.short_description = "Marquer présence comme faite"