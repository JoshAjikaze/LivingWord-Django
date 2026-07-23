from .models import SiteSettings


def site_settings(request):
    """
    Makes `site_settings` available in every template without each view
    having to fetch it explicitly (used in base.html's footer and the
    homepage hero copy).
    """
    return {"site_settings": SiteSettings.load()}
