from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from apps.books.models import Book


@override_settings(PUBLIC_SITE_URL="https://library.example.com")
class BookQrTests(TestCase):
    def create_book(self):
        return Book.objects.create(
            title="The QR Test Book",
            slug="the-qr-test-book",
            short_description="A QR test book.",
            description="Book description.",
        )

    def test_qr_code_is_generated_for_public_detail_url(self):
        book = self.create_book()

        self.assertTrue(book.qr_code)
        self.assertEqual(book.qr_target_url, "https://library.example.com/books/the-qr-test-book/")
        with book.qr_code.open("rb") as qr_file:
            self.assertEqual(qr_file.read(8), b"\x89PNG\r\n\x1a\n")

    def test_qr_code_is_regenerated_when_book_slug_changes(self):
        book = self.create_book()
        with book.qr_code.open("rb") as qr_file:
            original_png = qr_file.read()

        book.slug = "the-renamed-qr-book"
        book.save()
        book.refresh_from_db()

        self.assertEqual(book.qr_target_url, "https://library.example.com/books/the-renamed-qr-book/")
        with book.qr_code.open("rb") as qr_file:
            self.assertNotEqual(qr_file.read(), original_png)

    def test_public_book_detail_shows_qr_card_and_download(self):
        book = self.create_book()

        response = self.client.get(reverse("books:detail", args=[book.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "book-qr-card")
        self.assertContains(response, "Download QR code")
        self.assertContains(response, "library.example.com/books/the-qr-test-book/")

    def test_admin_uses_system_theme_with_built_in_toggle(self):
        self.assertEqual(settings.UNFOLD["THEME"], "auto")
        admin_user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_superuser(
            email="theme-admin@example.com",
            password="SecureP@ss1",
            name="Theme Admin",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toggle dark/light mode")

    def test_book_admin_exposes_qr_preview_target_and_download(self):
        admin = self.create_book()
        user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_superuser(
            email="qr-admin@example.com",
            password="SecureP@ss1",
            name="QR Admin",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:books_book_change", args=[admin.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QR target URL")
        self.assertContains(response, "Download PNG")
        self.assertContains(response, "library.example.com/books/the-qr-test-book/")
