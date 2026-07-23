from django.contrib.sitemaps import Sitemap

from .models import Book


class BookSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Book.objects.filter(status=Book.Status.AVAILABLE)

    def lastmod(self, obj):
        return obj.updated_at
