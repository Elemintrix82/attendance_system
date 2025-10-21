from django.contrib import admin
from .models import RapportPresence, StatistiqueCache


# Admin pour RapportPresence
@admin.register(RapportPresence)
class RapportPresenceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_rapport', 'format_fichier', 'genere_par', 
                   'date_generation', 'taille_fichier_display', 'telecharger')
    search_fields = ('titre', 'genere_par__username')
    list_filter = ('type_rapport', 'format_fichier', 'date_generation')
    ordering = ('-date_generation',)
    readonly_fields = ('date_generation', 'taille_fichier', 'nombre_pages', 'genere_par')
    date_hierarchy = 'date_generation'
    
    fieldsets = (
        ('Informations du rapport', {
            'fields': ('titre', 'type_rapport', 'format_fichier')
        }),
        ('Filtres appliqués', {
            'fields': ('etudiant', 'cours', 'filiere', 'niveau', 
                      'date_debut', 'date_fin')
        }),
        ('Fichier généré', {
            'fields': ('fichier', 'nombre_pages', 'taille_fichier')
        }),
        ('Métadonnées', {
            'fields': ('genere_par', 'date_generation'),
            'classes': ('collapse',)
        }),
    )
    
    def taille_fichier_display(self, obj):
        if obj.taille_fichier:
            if obj.taille_fichier < 1024:
                return f"{obj.taille_fichier} octets"
            elif obj.taille_fichier < 1024 * 1024:
                return f"{obj.taille_fichier / 1024:.2f} Ko"
            else:
                return f"{obj.taille_fichier / (1024 * 1024):.2f} Mo"
        return '-'
    taille_fichier_display.short_description = "Taille"
    
    def telecharger(self, obj):
        if obj.fichier:
            return f'<a href="{obj.fichier.url}" target="_blank" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📥 Télécharger</a>'
        return '-'
    telecharger.short_description = "Fichier"
    telecharger.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        if not obj.genere_par:
            obj.genere_par = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['supprimer_rapports']
    
    def supprimer_rapports(self, request, queryset):
        count = queryset.count()
        for rapport in queryset:
            if rapport.fichier:
                rapport.fichier.delete()
            rapport.delete()
        self.message_user(request, f'{count} rapport(s) supprimé(s).')
    supprimer_rapports.short_description = "Supprimer les rapports (et fichiers)"


# Admin pour StatistiqueCache
@admin.register(StatistiqueCache)
class StatistiqueCacheAdmin(admin.ModelAdmin):
    list_display = ('cle', 'date_calcul', 'date_expiration', 'est_expire_display')
    search_fields = ('cle',)
    list_filter = ('date_calcul', 'date_expiration')
    ordering = ('-date_calcul',)
    readonly_fields = ('cle', 'valeur', 'date_calcul')
    
    fieldsets = (
        ('Cache', {
            'fields': ('cle', 'valeur')
        }),
        ('Dates', {
            'fields': ('date_calcul', 'date_expiration')
        }),
    )
    
    def est_expire_display(self, obj):
        if obj.est_expire():
            return '<span style="color: red;">✗ Expiré</span>'
        return '<span style="color: green;">✓ Valide</span>'
    est_expire_display.short_description = "État"
    est_expire_display.allow_tags = True
    
    actions = ['vider_cache', 'supprimer_expires']
    
    def vider_cache(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} entrée(s) de cache supprimée(s).')
    vider_cache.short_description = "Vider le cache sélectionné"
    
    def supprimer_expires(self, request, queryset):
        from django.utils import timezone
        count = 0
        for cache in queryset:
            if cache.est_expire():
                cache.delete()
                count += 1
        self.message_user(request, f'{count} cache(s) expiré(s) supprimé(s).')
    supprimer_expires.short_description = "Supprimer les caches expirés"