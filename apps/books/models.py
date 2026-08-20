from decimal import Decimal
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        AVAILABLE = "available", "Available"
        RESTRICTED = "restricted", "Restricted"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    author_name = models.CharField(
        max_length=150,
        default="",
        blank=True,
        help_text="Display name on the book page. Leave blank to use the site's Author Profile name.",
    )
    isbn = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="ISBN",
        help_text="Optional ISBN-10 or ISBN-13 identifier.",
    )
    short_description = models.CharField(
        max_length=160,
        help_text="One line shown on the homepage and books grid cards.",
    )
    description = models.TextField(help_text="Full description shown on the book's own page.")
    whats_inside = models.TextField(
        blank=True,
        help_text="'What you'll find inside' section on the book page.",
    )
    cover_image = models.ImageField(upload_to="covers/")
    ebook_file = models.FileField(
        upload_to="ebooks/",
        blank=True,
        help_text="Full paid ebook file. Accepts PDF or EPUB. Keep this file protected in production.",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "epub"])],
    )
    sample_excerpt = models.FileField(
        upload_to="samples/",
        blank=True,
        help_text="Optional public sample chapter/excerpt. Accepts PDF or EPUB.",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "epub"])],
    )
    qr_code = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        editable=False,
        help_text="Automatically generated QR code for this book's public detail page.",
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0–100. Applied to price while discount_active_until is in the future.",
    )
    discount_active_until = models.DateTimeField(
        null=True, blank=True, help_text="Discount stops applying automatically after this date."
    )
    amazon_store_url = models.URLField(
        blank=True,
        default="",
        verbose_name="Amazon store URL",
        help_text="Optional outbound Amazon listing URL shown on the book detail page.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("books:detail", args=[self.slug])

    @property
    def qr_target_url(self):
        """Absolute URL encoded in the QR code."""
        base_url = getattr(settings, "PUBLIC_SITE_URL", "http://localhost:8000").rstrip("/")
        return f"{base_url}{self.get_absolute_url()}"

    def generate_qr_code(self):
        """Create or replace the QR image for the current public book URL."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_target_url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#5a1b1e", back_color="white")

        output = BytesIO()
        image.save(output, format="PNG")
        if self.qr_code:
            self.qr_code.delete(save=False)
        filename = f"book-{self.pk}.png"
        self.qr_code.save(filename, ContentFile(output.getvalue()), save=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_qr_code()
        super().save(update_fields=["qr_code", "updated_at"])

    @property
    def discount_is_active(self):
        if not self.discount_percent:
            return False
        if self.discount_active_until and self.discount_active_until < timezone.now():
            return False
        return True

    @property
    def display_price(self):
        """Price after discount, if the discount is currently active."""
        if not self.discount_is_active:
            return self.price
        discount_amount = (self.price * self.discount_percent) / Decimal("100")
        return (self.price - discount_amount).quantize(Decimal("0.01"))

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE


class BuyLink(models.Model):
    book = models.ForeignKey(Book, related_name="buy_links", on_delete=models.CASCADE)
    platform = models.CharField(max_length=80, help_text="e.g. Amazon, Apple Books, Barnes & Noble")
    url = models.URLField()
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers show first.")

    class Meta:
        ordering = ["order", "platform"]

    def __str__(self):
        return f"{self.platform} — {self.book.title}"
