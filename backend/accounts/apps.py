from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        try:
            from django.core.management import call_command
            call_command('migrate', interactive=False)
        except Exception:
            pass
