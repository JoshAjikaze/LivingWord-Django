from django.views.generic import DetailView, ListView

from .models import Book


class BookListView(ListView):
    model = Book
    template_name = "books/list.html"
    context_object_name = "books"

    def get_queryset(self):
        return Book.objects.filter(status=Book.Status.AVAILABLE)


class BookDetailView(DetailView):
    model = Book
    template_name = "books/detail.html"
    context_object_name = "book"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # Restricted/draft books are still viewable by direct admin preview
        # but excluded from the public queryset used elsewhere; here we allow
        # any status through so a "restricted" page can render its own
        # unavailable messaging rather than 404ing.
        return Book.objects.all()
