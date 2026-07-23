import io
import textwrap
from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.books.models import Book, BuyLink
from apps.core.models import AuthorProfile, SiteSettings

# (background, text) hex pairs — rotated across the 6 covers so the grid
# doesn't look monotonous before real cover art is uploaded.
PALETTE = [
    ("#FDF6EA", "#5A1B1E"),  # cream / wine
    ("#5A1B1E", "#FDF6EA"),  # wine / cream
    ("#FDF6EA", "#1F3A5F"),  # cream / navy
    ("#F5E6C8", "#5A1B1E"),  # deep parchment / wine
    ("#1F3A5F", "#FDF6EA"),  # navy / cream
    ("#C68A2E", "#411214"),  # gold / wine-dark
]

BOOKS = [
    {
        "title": "Call Him by His Names",
        "short_description": "Encounter God through the power and meaning of His Hebrew names.",
        "description": (
            "A devotional journey through the names of God as revealed in Scripture — "
            "Jehovah Jireh, El Shaddai, Yahweh Rapha — and what each one means for the "
            "seasons you're walking through right now."
        ),
        "whats_inside": "30 daily readings, each centered on one name of God, its Hebrew "
        "root, and a guided reflection for applying it to your week.",
        "price": Decimal("14.99"),
        "discount_percent": 0,
    },
    {
        "title": "Lives That Still Speak",
        "short_description": "68 biblical lives, one enduring lesson each: faith speaks louder than circumstance.",
        "description": (
            "From Abraham to Priscilla, this collection walks through the lives of 68 "
            "biblical figures — not as distant history, but as living proof that "
            "ordinary faith still speaks into extraordinary circumstance."
        ),
        "whats_inside": "68 short biographical devotions organized by theme: faith under "
        "pressure, obedience, restoration, and legacy.",
        "price": Decimal("16.99"),
        "discount_percent": 15,
    },
    {
        "title": "Faith-Rooted Affirmations & Declarations",
        "short_description": "Scripture-based declarations to anchor your faith, family, and household.",
        "description": (
            "A companion of daily declarations drawn directly from Scripture, written to "
            "be spoken aloud over your life, your family, and your home."
        ),
        "whats_inside": "12 thematic sections (identity, provision, healing, protection, "
        "household) with declarations formatted for daily reading.",
        "price": Decimal("12.99"),
        "discount_percent": 0,
    },
    {
        "title": "Prayers That Move Mountains",
        "short_description": "A 21-day guided prayer journey for seasons that feel immovable.",
        "description": (
            "Written for the seasons where prayer feels heavy — this guide walks through "
            "21 days of Scripture-anchored prayers for breakthrough, patience, and trust."
        ),
        "whats_inside": "21 daily prayer guides, each paired with a supporting passage and "
        "a short reflection prompt.",
        "price": Decimal("13.99"),
        "discount_percent": 0,
    },
    {
        "title": "Seasons of the Heart",
        "short_description": "A quiet devotional for grief, waiting, and renewal.",
        "description": (
            "For the reader in a season of waiting — this devotional sits with grief, "
            "uncertainty, and slow renewal without rushing toward easy answers."
        ),
        "whats_inside": "40 reflections organized into four 'seasons': lament, waiting, "
        "rebuilding, and renewal.",
        "price": Decimal("15.99"),
        "discount_percent": 20,
    },
    {
        "title": "The Language of His Presence",
        "short_description": "Learning to recognize God's voice in the everyday and the ordinary.",
        "description": (
            "A practical guide to recognizing God's presence outside of the dramatic — "
            "in routine, in rest, and in the quiet parts of an ordinary day."
        ),
        "whats_inside": "8 weeks of daily readings built around a single practice: "
        "noticing, naming, and responding to God's presence in daily life.",
        "price": Decimal("14.99"),
        "discount_percent": 0,
    },
]


def generate_cover(title: str, bg_hex: str, text_hex: str) -> ContentFile:
    """
    Simple placeholder cover: solid color field + wrapped title text.
    Meant to be replaced with real cover art via the admin — see README.
    """
    width, height = 600, 880
    img = Image.new("RGB", (width, height), bg_hex)
    draw = ImageDraw.Draw(img)

    # Thin border to read as a "cover" rather than a flat swatch
    draw.rectangle([20, 20, width - 20, height - 20], outline=text_hex, width=3)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 42)
    except OSError:
        font = ImageFont.load_default()

    wrapped = textwrap.wrap(title, width=14)
    line_height = 54
    total_height = len(wrapped) * line_height
    y = (height - total_height) / 2

    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) / 2
        draw.text((x, y), line, font=font, fill=text_hex)
        y += line_height

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"{title.lower().replace(' ', '-')}.jpg")


class Command(BaseCommand):
    help = "Seeds SiteSettings, an AuthorProfile, and 6 demo books with placeholder cover art."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing Book/BuyLink records before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            Book.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing books."))

        SiteSettings.load()
        self.stdout.write(self.style.SUCCESS("SiteSettings ready."))

        author, created = AuthorProfile.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Author Name",
                "bio": (
                    "Replace this with the real author bio via /admin/ — "
                    "this is placeholder text generated by the seed command."
                ),
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("AuthorProfile created (placeholder bio)."))

        for i, data in enumerate(BOOKS):
            slug = data["title"].lower().replace(" ", "-").replace("&", "and").replace("--", "-")
            bg_hex, text_hex = PALETTE[i % len(PALETTE)]

            book, created = Book.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "short_description": data["short_description"],
                    "description": data["description"],
                    "whats_inside": data["whats_inside"],
                    "price": data["price"],
                    "discount_percent": data["discount_percent"],
                    "discount_active_until": (
                        timezone.now() + timedelta(days=14) if data["discount_percent"] else None
                    ),
                    "status": Book.Status.AVAILABLE,
                    "published_at": timezone.now() - timedelta(days=(6 - i) * 7),
                },
            )

            if created:
                book.cover_image.save(
                    f"{slug}.jpg",
                    generate_cover(data["title"], bg_hex, text_hex),
                    save=True,
                )
                BuyLink.objects.create(
                    book=book, platform="Amazon", url="https://amazon.com/", order=0
                )
                self.stdout.write(self.style.SUCCESS(f"Created: {book.title}"))
            else:
                self.stdout.write(f"Skipped (already exists): {book.title}")

        self.stdout.write(self.style.SUCCESS("Done. Run the dev server and visit / to see it."))
