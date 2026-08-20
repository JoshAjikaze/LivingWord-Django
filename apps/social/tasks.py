from django.db.models import Q
from django.utils import timezone

from .models import SocialDelivery
from .services import process_delivery


def process_due_deliveries(limit=20):
    now = timezone.now()
    deliveries = SocialDelivery.objects.filter(
        Q(status=SocialDelivery.Status.QUEUED) | Q(status=SocialDelivery.Status.FAILED, next_attempt_at__lte=now),
        Q(post__scheduled_at__isnull=True) | Q(post__scheduled_at__lte=now),
    ).filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now)).order_by("created_at")[:limit]
    return [process_delivery(delivery.pk) for delivery in deliveries]
