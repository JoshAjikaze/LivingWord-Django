from django import forms


class _SignupFormStub(forms.Form):
    """
    Placeholder class that allauth's flow loader finds during module import.
    It carries the required `signup()` hook plus the `by_passkey` attribute
    the signup view expects, and is swapped for the real BaseSignupForm-
    derived form in AccountsConfig.ready() — after allauth's own modules
    are initialized.
    """

    by_passkey = False

    def signup(self, request, user):
        pass


class SignupForm(_SignupFormStub):
    """
    Signup form for the custom User model: replaces the allauth `username`
    field with a `name` (display name) field, which the adapter persists
    onto the custom User model's `name` attribute.

    The real allauth BaseSignupForm is attached as a base class below, once
    allauth has finished its own module setup.
    """

    name = forms.CharField(
        label="Name",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        # Keep the declared field order: name, email, password1, password2
        if set(self.fields) >= {"name", "email", "password1"}:
            self.order_fields(["name", "email", "password1", "password2"])

    def signup(self, request, user):
        # Persisted by the adapter's save_user; kept as a hook for any future
        # post-save logic (e.g., welcome notifications).
        pass


# ---------------------------------------------------------------------------
# Promote the stub to inherit from allauth's real BaseSignupForm. Doing this
# at import time here would re-trigger the circular import (allauth resolves
# this very module to build BaseSignupForm), so the swap runs inside
# AccountsConfig.ready() — after allauth's modules are fully initialized.
# ---------------------------------------------------------------------------

def build_signup_form():
    """
    Build the real SignupForm by subclassing allauth's own SignupForm (which
    carries the by_passkey handling the signup view expects). This runs from
    AccountsConfig.ready() — after allauth's modules are fully initialized —
    avoiding the circular import that occurs because allauth itself imports
    this module to resolve its own base class.
    """
    from allauth.account.forms import SignupForm as _AllauthSignupForm

    class SignupForm(_AllauthSignupForm):
        name = forms.CharField(
            label="Name",
            max_length=150,
            required=True,
            widget=forms.TextInput(
                attrs={"placeholder": "Your name", "autocomplete": "name"}
            ),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields.pop("username", None)
            if set(self.fields) >= {"name", "email", "password1"}:
                self.order_fields(["name", "email", "password1", "password2"])

        def signup(self, request, user):
            # Persisted by the adapter's save_user; kept as a hook for any
            # future post-save logic (e.g., welcome notifications).
            pass

    return SignupForm


# Allauth resolves SIGNUP_FORM_CLASS by `import_module`, which triggers
# module evaluation. During that first import we cannot yet subclass
# BaseSignupForm (circular), so expose a class-shaped placeholder now.
SignupForm = _SignupFormStub


def _finalize_signup_form():
    """Swap the placeholder for the real allauth SignupForm-derived form."""
    global SignupForm
    SignupForm = build_signup_form()
