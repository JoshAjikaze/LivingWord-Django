# Visual verification findings (Aug 16)

## Home page (/)
- All sections render: hero, stacked covers, mission, collection preview with 3 seeded books, footer.
- Nav shows "Sign in" (btn-outline) + "Create account" (btn-gold). Design language matches.

## Signup (/accounts/signup/)
- Two-column layout with brand panel + auth card works.
- ISSUE: password help_text renders as plain paragraphs inside the card (all 4 validators shown as stacked serif text) — needs auth-hint styling; the hint is Django's full help text, better to wrap in a ul with auth-hint class. Minor, fixable.
- ISSUE: social login panel did NOT render — "or continue with" divider + Google/Facebook buttons missing. Need to check why: possibly `get_providers` empty because SocialApp rows missing, or template loading order (provider_login_url from allauth). Investigate.

## To verify still
- login page, verification page, post-signup flow, social buttons root cause.
