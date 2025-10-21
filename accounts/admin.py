from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profil, HistoriqueConnexion


# Inline pour afficher le profil dans l'admin User
class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name = 'Profil'
    verbose_name_plural = 'Profils'
    fk_name = 'user'
    fields = ('role', 'telephone', 'adresse', 'photo', 'actif')


# Étendre l'admin User de Django
class UserAdmin(BaseUserAdmin):
    inlines = (ProfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profil__role')
    
    def get_role(self, obj):
        if hasattr(obj, 'profil'):
            return obj.profil.get_role_display()
        return '-'
    get_role.short_description = 'Rôle'


# Réenregistrer UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Admin pour Profil
@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'telephone', 'actif', 'date_creation')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 
                    'telephone')
    list_filter = ('role', 'actif', 'date_creation')
    ordering = ('user__username',)
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'role', 'actif')
        }),
        ('Contact', {
            'fields': ('telephone', 'adresse', 'photo')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activer_profils', 'desactiver_profils']
    
    def activer_profils(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} profil(s) activé(s).')
    activer_profils.short_description = "Activer les profils sélectionnés"
    
    def desactiver_profils(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} profil(s) désactivé(s).')
    desactiver_profils.short_description = "Désactiver les profils sélectionnés"


# Admin pour HistoriqueConnexion
@admin.register(HistoriqueConnexion)
class HistoriqueConnexionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_connexion', 'ip_address')
    search_fields = ('user__username', 'ip_address')
    list_filter = ('date_connexion',)
    ordering = ('-date_connexion',)
    readonly_fields = ('user', 'date_connexion', 'ip_address', 'user_agent')
    date_hierarchy = 'date_connexion'
    
    def has_add_permission(self, request):
        # Empêcher l'ajout manuel
        return False
    
    def has_change_permission(self, request, obj=None):
        # Lecture seule
        return False