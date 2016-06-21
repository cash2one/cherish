from django.apps import AppConfig


class AuthUserConfig(AppConfig):
    name = 'auth_user'

    # override
    def ready(self):
        import signals
