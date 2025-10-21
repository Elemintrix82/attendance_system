from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Comptes utilisateurs'
    
    def ready(self):
        """Importer les signals quand l'app est prête"""
        import accounts.signals