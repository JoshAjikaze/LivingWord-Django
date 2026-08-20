from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter for the email-as-username user model. allauth 65.x's default
    adapter works with the user model's own `USERNAME_FIELD` already, but
    `save_user()` reads a `username` key from cleaned data — this adapter
    routes the signup `name` field into the custom User model's `name`
    attribute instead, and skips username population entirely.
    """

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        # The custom User model has no `username`; the signup form carries the
        # display name in `name`, which we persist here.
        name = form.cleaned_data.get("name")
        if name:
            user.name = name
        if commit:
            user.save()
        return user

    def populate_username(self, request, user):
        # No username field on the user model — leave it unset.
        pass
