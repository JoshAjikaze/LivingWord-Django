from django.core.management.base import BaseCommand

from apps.books.models import Book


class Command(BaseCommand):
    help = "Regenerate book QR codes using the current PUBLIC_SITE_URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            help="Regenerate only the book matching this slug.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List the QR targets without changing stored images.",
        )

    def handle(self, *args, **options):
        books = Book.objects.all().order_by("pk")
        if options.get("slug"):
            books = books.filter(slug=options["slug"])

        count = 0
        for book in books.iterator():
            target = book.qr_target_url
            if options["dry_run"]:
                self.stdout.write(f"{book.pk}: {target}")
                count += 1
                continue

            book.generate_qr_code()
            book.save(update_fields=["qr_code", "updated_at"])
            self.stdout.write(self.style.SUCCESS(f"Regenerated {book.title}: {target}"))
            count += 1

        if not count:
            self.stdout.write(self.style.WARNING("No matching books found."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Processed {count} book QR code(s)."))
