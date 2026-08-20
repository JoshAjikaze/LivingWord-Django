from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.books.models import Book
from apps.core.models import AuthorProfile


class AboutPageTests(TestCase):
    def test_about_page_matches_editorial_design_content(self):
        response = self.client.get(reverse("core:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The heart behind the library")
        self.assertContains(response, "About the author")
        self.assertContains(response, "The Living Word Library was born from a simple conviction")
        self.assertContains(response, "about-author-page__story")

    def test_about_page_renders_author_profile_when_available(self):
        AuthorProfile.objects.create(
            name="Jane Author",
            bio="A short author biography.",
        )

        response = self.client.get(reverse("core:about"))

        self.assertContains(response, "Jane Author")
        self.assertContains(response, "A short author biography.")


class RefreshQrCodesCommandTests(TestCase):
    @override_settings(PUBLIC_SITE_URL="https://new-library.example.com")
    def test_refresh_command_uses_current_public_site_url(self):
        book = Book.objects.create(
            title="Refresh Test Book",
            slug="refresh-test-book",
            short_description="A refresh test book.",
            description="Book description.",
        )
        output = StringIO()

        call_command("refresh_qr_codes", stdout=output)

        book.refresh_from_db()
        self.assertEqual(book.qr_target_url, "https://new-library.example.com/books/refresh-test-book/")
        self.assertIn("https://new-library.example.com/books/refresh-test-book/", output.getvalue())
