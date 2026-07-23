from django.views.generic import TemplateView

from apps.books.models import Book
from .models import AuthorProfile


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_books"] = (
            Book.objects.filter(status="available").order_by("-published_at")[:3]
        )
        return context


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = AuthorProfile.objects.first()
        return context
