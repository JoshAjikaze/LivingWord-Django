from django.core.management.base import BaseCommand

from apps.social.tasks import process_due_deliveries


class Command(BaseCommand):
    help = "Publish due and retryable social deliveries. Run from cron or a worker process."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        deliveries = process_due_deliveries(limit=options["limit"])
        successes = sum(delivery.status == "success" for delivery in deliveries)
        failures = sum(delivery.status == "failed" for delivery in deliveries)
        self.stdout.write(self.style.SUCCESS(f"Processed {len(deliveries)} deliveries: {successes} succeeded, {failures} failed."))
