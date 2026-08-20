# Task state — Homepage + Auth screens (LivingWord Library)

Working dir: /home/ubuntu/livingword-django (copied from project zip). Dev server running on :8000 (log: /tmp/django.log). SQLite db seeded via `python3 manage.py seed_demo_data`.

## Done
- apps.accounts created: custom User (email=USERNAME_FIELD, role CUSTOMER/ADMIN), UserManager, adapters.CustomAccountAdapter (save_user stores name), forms.SignupForm (name field, drops username, base class promoted via _promote_base_class() called from AccountsConfig.ready()), urls.py (account:profile), views.profile_view, admin UserAdmin (Unfold).
- settings/base.py: SITE_ID=1, allauth apps+providers (google, facebook), AUTH_USER_MODEL=accounts.User, ACCOUNT_LOGIN_METHODS={"email"}, ACCOUNT_SIGNUP_FIELDS=["email*","password1*","password2*"], ACCOUNT_SIGNUP_FORM_CLASS=apps.accounts.forms.SignupForm, ACCOUNT_EMAIL_VERIFICATION="mandatory", ACCOUNT_ADAPTER, LOGIN_REDIRECT_URL=account_profile, LOGOUT_REDIRECT_URL=core:home, AccountMiddleware added.
- settings/dev.py: plain StaticFilesStorage override (avoid whitenoise manifest in dev/tests).
- Templates: templates/account/{_auth_base.html, login, signup, logout, email_confirm, verification_sent, email, password_reset, password_reset_done, password_reset_from_key, password_reset_from_key_done, password_change, password_set}. Templates/accounts/profile.html. templates/account/email/{email_confirmation_subject.txt, email_confirmation_message.txt, email_confirmation_signup_subject.txt, password_reset_subject.txt, password_reset_message.txt}. templates/account/_social_login.html (Google/Facebook buttons via provider_login_url).
- templates/partials/_nav.html: auth-aware (Sign in / Create account for anon; Hello/name, My account, Admin link for admins, Log out for logged in).
- static/css/input.css: added auth-card, auth-field, auth-label, auth-errorlist, auth-hint, social-btn styles. Rebuilt output.css via `npm run build:css`.
- SocialApp rows for google+facebook (PLACEHOLDER creds) + Site id=1 created via manage.py shell (dev db).
- tests/test_auth_flow.py: 11 tests (homepage, nav ctas, signup creates customer, dup email, unverified login, password validators, login page, social panel, profile requires login, authenticated nav, admin link).
- Home page screenshot verified: good. Login page: good with social buttons. Signup: fixed password help text into list; social panel appears once SocialApps exist.

## Resolved issues (record)
- ACCOUNT_SIGNUP_FORM_CLASS deprecated/broken → use ACCOUNT_FORMS={"signup": "apps.accounts.forms.SignupForm"}.
- SignupForm circular-import fix: placeholder stub (by_passkey=False + signup hook) swapped in ready() via _finalize_signup_form(); final class subclasses allauth's SignupForm (has by_passkey).
- url name 'account_profile' → 'account:profile' (namespace account).
- STORAGES override in dev.py for plain StaticFilesStorage.
- All 11 pytest tests pass; `manage.py check` clean. Signup page verified visually: name/email/password fields + Google/Facebook social buttons render.
- tests/e2e_verify.py: browser test signup→confirm-email page done; uses EmailConfirmation model for key. Run it next.

## Done (e2e)
- e2e_verify.py passes: signup → confirm-email (HMAC key via EmailConfirmationHMAC.create) → confirm → login → profile (Hello, Grace Reader / My account / Log out). Screenshots: tests/shots/{home,signup,login,password_reset,books_list,email_confirmed,profile}.png all verified.
- Profile page shows account type Customer, member since, my purchases empty state, account settings links.

## Remaining
- Add dev notes to README (SocialApp setup, console email backend in dev, verification flow).
- Zip /home/ubuntu/livingword-django → livingword-django.zip and deliver with summary + key screenshots.

## Key remaining decisions
- Run `python3 manage.py check` clean.
- Deliverable: zip of /home/ubuntu/livingword-django.
