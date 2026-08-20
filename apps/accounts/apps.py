from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"

    def ready(self):
        # After allauth's modules are fully initialized, build the real
        # custom SignupForm on top of allauth's BaseSignupForm (see the
        # circular-import note in apps.accounts.forms).
        from apps.accounts.forms import _finalize_signup_form  # noqa

        _finalize_signup_form()
