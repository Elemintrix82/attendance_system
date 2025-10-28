from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Salle, Cours, HoraireCours, SeanceCours
from students.models import Filiere
from teachers.models import Enseignant


# ============================================
# INLINE POUR LES HORAIRES DE COURS
# ============================================

class HoraireCoursInline(admin.TabularInline):
    """Inline pour gérer les horaires d'un cours directement depuis l'admin Cours"""
    model = HoraireCours
    extra = 1
    fields = ('jour_semaine', 'heure_debut', 'heure_fin', 'salle', 'type_seance', 'remarque', 'actif')
    ordering = ['jour_semaine', 'heure_debut']
    verbose_name = "Horaire"
    verbose_name_plural = "Horaires du cours"
    autocomplete_fields = ['salle']


# ============================================
# RESOURCES POUR IMPORT/EXPORT
# ============================================

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
        fields = ('id', 'code', 'intitule', 'description', 'filiere',
                 'enseignant', 'salle', 'semestre', 'annee_academique', 
                 'credits', 'coefficient', 'volume_horaire_cm', 
                 'volume_horaire_td', 'volume_horaire_tp', 'actif')
        export_order = ('code', 'intitule', 'filiere', 'enseignant',
                       'semestre', 'annee_academique', 'salle', 'credits', 
                       'coefficient', 'actif')
        import_id_fields = ['code', 'annee_academique']
        skip_unchanged = True


class HoraireCoursResource(resources.ModelResource):
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
        model = HoraireCours
        fields = ('id', 'cours', 'jour_semaine', 'heure_debut', 'heure_fin',
                 'salle', 'type_seance', 'remarque', 'actif')
        export_order = ('cours', 'jour_semaine', 'heure_debut', 'heure_fin',
                       'type_seance', 'salle', 'actif')
        import_id_fields = ['cours', 'jour_semaine', 'heure_debut']
        skip_unchanged = True


class SeanceCoursResource(resources.ModelResource):
    cours = resources.Field(
        column_name='cours_code',
        attribute='cours',
        widget=resources.widgets.ForeignKeyWidget(Cours, 'code')
    )
    horaire_cours = resources.Field(
        column_name='horaire_cours_id',
        attribute='horaire_cours',
        widget=resources.widgets.ForeignKeyWidget(HoraireCours, 'id')
    )
    salle = resources.Field(
        column_name='salle',
        attribute='salle',
        widget=resources.widgets.ForeignKeyWidget(Salle, 'nom')
    )
    
    class Meta:
        model = SeanceCours
        fields = ('id', 'cours', 'horaire_cours', 'date', 'heure_debut', 'heure_fin', 
                 'salle', 'type_seance', 'contenu', 'presente', 'annulee')
        export_order = ('cours', 'date', 'heure_debut', 'heure_fin', 
                       'salle', 'type_seance', 'presente', 'annulee')
        import_id_fields = ['cours', 'date', 'heure_debut']
        skip_unchanged = True


# ============================================
# MODEL ADMINS
# ============================================

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
            'fields': ('equipements', 'remarque')
        }),
    )
    
    def nombre_cours(self, obj):
        return obj.cours.filter(actif=True).count()
    nombre_cours.short_description = "Nb cours"
    
    actions = ['rendre_disponible', 'rendre_indisponible']
    
    def rendre_disponible(self, request, queryset):
        updated = queryset.update(disponible=True)
        self.message_user(request, f'✅ {updated} salle(s) rendue(s) disponible(s).')
    rendre_disponible.short_description = "✅ Rendre disponible"
    
    def rendre_indisponible(self, request, queryset):
        updated = queryset.update(disponible=False)
        self.message_user(request, f'⛔ {updated} salle(s) rendue(s) indisponible(s).')
    rendre_indisponible.short_description = "⛔ Rendre indisponible"


@admin.register(Cours)
class CoursAdmin(ImportExportModelAdmin):
    resource_class = CoursResource
    inlines = [HoraireCoursInline]  # ✅ AJOUT DE L'INLINE
    
    list_display = ('code', 'intitule', 'filiere_complete', 'enseignant',
                   'semestre', 'annee_academique', 'credits', 'volume_total', 
                   'nombre_horaires', 'actif', 'nb_seances')
    search_fields = ('code', 'intitule', 'enseignant__nom', 'enseignant__prenom', 
                    'filiere__code')
    list_filter = ('filiere__specialite', 'filiere__formation', 'filiere__niveau',
                  'semestre', 'annee_academique', 'actif')
    ordering = ('code',)
    readonly_fields = ('date_creation', 'date_modification')
    autocomplete_fields = ['filiere', 'enseignant', 'salle']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('code', 'intitule', 'description', 'actif')
        }),
        ('Affectation académique', {
            'fields': ('filiere', 'semestre', 'annee_academique')
        }),
        ('Enseignant et salle', {
            'fields': ('enseignant', 'salle'),
            'description': 'La salle ici est la salle principale. Chaque horaire peut avoir sa propre salle.'
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
    
    def filiere_complete(self, obj):
        """Affiche la filière complète (Spécialité + Formation + Niveau)"""
        return obj.filiere.nom_complet()
    filiere_complete.short_description = "Filière"
    filiere_complete.admin_order_field = 'filiere__code'
    
    def volume_total(self, obj):
        total = obj.get_volume_horaire_total()
        return f"{total}h"
    volume_total.short_description = "Volume total"
    
    def nombre_horaires(self, obj):
        """Affiche le nombre d'horaires du cours"""
        count = obj.horaires.filter(actif=True).count()
        if count == 0:
            return '<span style="color: red;">⚠️ Aucun</span>'
        return f'<span style="color: green;">✓ {count}</span>'
    nombre_horaires.short_description = "Horaires"
    nombre_horaires.allow_tags = True
    
    def nb_seances(self, obj):
        return obj.get_nombre_seances()
    nb_seances.short_description = "Nb séances"
    
    actions = ['activer_cours', 'desactiver_cours']
    
    def activer_cours(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'✅ {updated} cours activé(s).')
    activer_cours.short_description = "✅ Activer les cours sélectionnés"
    
    def desactiver_cours(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'⛔ {updated} cours désactivé(s).')
    desactiver_cours.short_description = "⛔ Désactiver les cours sélectionnés"


@admin.register(HoraireCours)
class HoraireCoursAdmin(ImportExportModelAdmin):
    resource_class = HoraireCoursResource
    list_display = ('cours_display', 'jour_semaine', 'heure_debut', 'heure_fin',
                   'salle', 'type_seance', 'duree', 'actif')
    search_fields = ('cours__code', 'cours__intitule')
    list_filter = ('jour_semaine', 'type_seance', 'actif', 
                  'cours__filiere__specialite',
                  'cours__filiere__formation',
                  'cours__filiere__niveau')
    ordering = ('cours', 'jour_semaine', 'heure_debut')
    autocomplete_fields = ['cours', 'salle']
    
    fieldsets = (
        ('Cours', {
            'fields': ('cours',)
        }),
        ('Horaire', {
            'fields': ('jour_semaine', 'heure_debut', 'heure_fin', 'salle', 'type_seance')
        }),
        ('Options', {
            'fields': ('remarque', 'actif')
        }),
    )
    
    def cours_display(self, obj):
        return f"{obj.cours.code} - {obj.cours.intitule}"
    cours_display.short_description = "Cours"
    cours_display.admin_order_field = 'cours__code'
    
    def duree(self, obj):
        return f"{obj.get_duree()}h"
    duree.short_description = "Durée"
    
    actions = ['activer_horaires', 'desactiver_horaires']
    
    def activer_horaires(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'✅ {updated} horaire(s) activé(s).')
    activer_horaires.short_description = "✅ Activer les horaires"
    
    def desactiver_horaires(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'⛔ {updated} horaire(s) désactivé(s).')
    desactiver_horaires.short_description = "⛔ Désactiver les horaires"


@admin.register(SeanceCours)
class SeanceCoursAdmin(ImportExportModelAdmin):
    resource_class = SeanceCoursResource
    list_display = ('cours', 'date', 'heure_debut', 'heure_fin', 'type_seance', 
                   'salle', 'presente_display', 'annulee_display', 'taux_presence_display')
    search_fields = ('cours__code', 'cours__intitule')
    list_filter = ('type_seance', 'presente', 'annulee', 'date', 
                  'cours__filiere__specialite',
                  'cours__filiere__formation',
                  'cours__filiere__niveau')
    ordering = ('-date', '-heure_debut')
    readonly_fields = ('date_creation', 'date_modification')
    date_hierarchy = 'date'
    autocomplete_fields = ['cours', 'horaire_cours', 'salle']
    
    fieldsets = (
        ('Cours et horaires', {
            'fields': ('cours', 'horaire_cours', 'date', 'heure_debut', 'heure_fin', 'salle')
        }),
        ('Détails de la séance', {
            'fields': ('type_seance', 'contenu', 'presente')
        }),
        ('Annulation', {
            'fields': ('annulee', 'motif_annulation'),
            'classes': ('collapse',)
        }),
        ('Remarque', {
            'fields': ('remarque',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def presente_display(self, obj):
        if obj.presente:
            return '<span style="color: green; font-weight: bold;">✓ Effectuée</span>'
        return '<span style="color: orange;">⏳ En attente</span>'
    presente_display.short_description = "Présence"
    presente_display.allow_tags = True
    
    def annulee_display(self, obj):
        if obj.annulee:
            return '<span style="color: red;">✗ Annulée</span>'
        return '<span style="color: green;">✓ Maintenue</span>'
    annulee_display.short_description = "État"
    annulee_display.allow_tags = True
    
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
    
    actions = ['marquer_presente_faite', 'annuler_seances', 'reactiver_seances']
    
    def marquer_presente_faite(self, request, queryset):
        updated = queryset.update(presente=True)
        self.message_user(request, f'✅ Présence marquée comme faite pour {updated} séance(s).')
    marquer_presente_faite.short_description = "✅ Marquer présence comme faite"
    
    def annuler_seances(self, request, queryset):
        updated = queryset.update(annulee=True, motif_annulation="Annulation depuis l'admin")
        self.message_user(request, f'⛔ {updated} séance(s) annulée(s).')
    annuler_seances.short_description = "⛔ Annuler les séances"
    
    def reactiver_seances(self, request, queryset):
        updated = queryset.update(annulee=False, motif_annulation='')
        self.message_user(request, f'✅ {updated} séance(s) réactivée(s).')
    reactiver_seances.short_description = "✅ Réactiver les séances"