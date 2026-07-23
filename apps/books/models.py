from decimal import Decimal

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
    sample_excerpt = models.FileField(
        upload_to="samples/",
        blank=True,
        help_text="Optional sample chapter/excerpt (PDF/EPUB) offered on the book page.",
    )

    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    discount_percent = models.PositiveSmallIntegerField(
        default=0, help_text="0–100. Applied to price while discount_active_until is in the future."
    )
    discount_active_until = models.DateTimeField(
        null=True, blank=True, help_text="Discount stops applying automatically after this date."
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
