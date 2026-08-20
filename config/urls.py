from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.books.sitemaps import BookSitemap

sitemaps = {
    "books": BookSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("books/", include("apps.books.urls")),
    path("newsletter/", include("apps.newsletter.urls")),
    path("contact/", include("apps.contact.urls")),
    path("payments/", include("apps.payments.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
