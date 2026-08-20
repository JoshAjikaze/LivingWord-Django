from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from pathlib import Path

from django.urls import reverse

from apps.books.models import Book


class BookAdminUploadTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            email="book-admin@example.com",
            password="SecureP@ss1",
            name="Book Admin",
        )
        self.client.force_login(self.admin)

    def test_book_add_form_exposes_ebook_upload_fields(self):
        response = self.client.get(reverse("admin:books_book_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="ebook_file"')
        self.assertContains(response, 'name="sample_excerpt"')
        self.assertContains(response, "Amazon store URL")
        self.assertContains(response, "ISBN")

    def test_admin_can_create_book_with_pdf_and_excerpt(self):
        cover_path = Path(__file__).parent / "shots" / "home.png"
        with cover_path.open("rb") as cover_handle:
            cover_upload = SimpleUploadedFile(
                "cover.png", cover_handle.read(), content_type="image/png"
            )

        response = self.client.post(
            reverse("admin:books_book_add"),
            {
                "title": "A Test Book",
                "slug": "a-test-book",
                "author_name": "Test Author",
                "isbn": "9781234567890",
                "short_description": "A short test description.",
                "description": "A longer description for the test book.",
                "whats_inside": "Sample contents.",
                "price": "9.99",
                "discount_percent": "0",
                "discount_active_until": "",
                "amazon_store_url": "https://www.amazon.com/dp/TEST123",
                "status": "draft",
                "published_at": "",
                "cover_image": cover_upload,
                "_save": "Save",
                "ebook_file": SimpleUploadedFile(
                    "test-book.pdf", b"%PDF-1.4 test", content_type="application/pdf"
                ),
                "sample_excerpt": SimpleUploadedFile(
                    "excerpt.epub", b"PK test epub", content_type="application/epub+zip"
                ),
                "buy_links-TOTAL_FORMS": "0",
                "buy_links-INITIAL_FORMS": "0",
                "buy_links-MIN_NUM_FORMS": "0",
                "buy_links-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(response.status_code, 302)
        book = Book.objects.get(slug="a-test-book")
        self.assertEqual(book.isbn, "9781234567890")
        self.assertTrue(Path(book.ebook_file.name).name.startswith("test-book"))
        self.assertTrue(Path(book.ebook_file.name).name.endswith(".pdf"))
        self.assertTrue(Path(book.sample_excerpt.name).name.startswith("excerpt"))
        self.assertTrue(Path(book.sample_excerpt.name).name.endswith(".epub"))
        self.assertEqual(book.amazon_store_url, "https://www.amazon.com/dp/TEST123")
