import mimetypes
import time
from datetime import timedelta

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import SocialAccount, SocialDelivery, SocialPost


class SocialPublishError(Exception):
    pass


PLATFORM_LIMITS = {
    SocialAccount.Platform.FACEBOOK: 63206,
    SocialAccount.Platform.INSTAGRAM: 2200,
    SocialAccount.Platform.THREADS: 500,
    SocialAccount.Platform.YOUTUBE: 5000,
    SocialAccount.Platform.X: 280,
}


def public_asset_url(asset):
    if not asset.file:
        raise SocialPublishError("A selected media asset has no file.")
    if not getattr(settings, "PUBLIC_SITE_URL", "").startswith("https://"):
        raise SocialPublishError("Publishing requires PUBLIC_SITE_URL to be a public HTTPS URL.")
    return f"{settings.PUBLIC_SITE_URL.rstrip('/')}{asset.file.url}"


def validate_post(post, account):
    if len((post.body or "").strip()) > PLATFORM_LIMITS[account.platform]:
        raise SocialPublishError(f"{account.get_platform_display()} allows at most {PLATFORM_LIMITS[account.platform]} characters.")
    assets = list(post.assets.all())
    if account.platform == SocialAccount.Platform.YOUTUBE:
        if len(assets) != 1 or assets[0].media_type != "video":
            raise SocialPublishError("YouTube publishing requires exactly one video asset.")
        if not post.title.strip():
            raise SocialPublishError("YouTube publishing requires a video title.")
    if account.platform == SocialAccount.Platform.INSTAGRAM and not assets:
        raise SocialPublishError("Instagram publishing requires an image or video asset.")
    if account.platform == SocialAccount.Platform.X and len(assets) > 4:
        raise SocialPublishError("X supports at most four media attachments per post.")
    if account.platform == SocialAccount.Platform.THREADS and len(assets) > 20:
        raise SocialPublishError("Threads supports at most twenty carousel items.")


def provider_response(response):
    try:
        data = response.json()
    except ValueError:
        data = {"text": response.text[:2000]}
    if response.status_code >= 400:
        raise SocialPublishError(f"Provider returned HTTP {response.status_code}: {data}")
    return data


def publish_facebook(account, post):
    base = "https://graph.facebook.com/v23.0"
    assets = list(post.assets.all())
    if not assets:
        payload = {"message": post.body, "access_token": account.access_token}
        if post.link_url:
            payload["link"] = post.link_url
        return provider_response(requests.post(f"{base}/{account.external_id}/feed", data=payload, timeout=60))
    asset = assets[0]
    endpoint = "videos" if asset.media_type == "video" else "photos"
    text_key = "description" if endpoint == "videos" else "caption"
    payload = {"access_token": account.access_token, text_key: post.body}
    payload["file_url" if endpoint == "videos" else "url"] = public_asset_url(asset)
    return provider_response(requests.post(f"{base}/{account.external_id}/{endpoint}", data=payload, timeout=120))


def publish_instagram(account, post):
    base = "https://graph.facebook.com/v23.0"
    assets = list(post.assets.all())
    if len(assets) > 1:
        children = []
        for asset in assets:
            payload = {"is_carousel_item": "true", "access_token": account.access_token, "media_type": "VIDEO" if asset.media_type == "video" else "IMAGE"}
            payload["image_url" if asset.media_type == "image" else "video_url"] = public_asset_url(asset)
            children.append(provider_response(requests.post(f"{base}/{account.external_id}/media", data=payload, timeout=120))["id"])
        container = {"media_type": "CAROUSEL", "children": ",".join(children), "caption": post.body, "access_token": account.access_token}
    else:
        asset = assets[0]
        container = {"caption": post.body, "access_token": account.access_token}
        container["image_url" if asset.media_type == "image" else "video_url"] = public_asset_url(asset)
        if asset.media_type == "video":
            container["media_type"] = "REELS"
    creation_id = provider_response(requests.post(f"{base}/{account.external_id}/media", data=container, timeout=120))["id"]
    for _ in range(12):
        status = provider_response(requests.get(f"{base}/{creation_id}", params={"fields": "status_code", "access_token": account.access_token}, timeout=30))
        if status.get("status_code") in {"FINISHED", "PUBLISHED"}:
            break
        if status.get("status_code") == "ERROR":
            raise SocialPublishError(f"Instagram media processing failed: {status}")
        time.sleep(5)
    return provider_response(requests.post(f"{base}/{account.external_id}/media_publish", data={"creation_id": creation_id, "access_token": account.access_token}, timeout=60))


def publish_threads(account, post):
    base = "https://graph.threads.com/v1.0"
    assets = list(post.assets.all())
    payload = {"text": post.body, "access_token": account.access_token}
    if assets:
        asset = assets[0]
        payload["image_url" if asset.media_type == "image" else "video_url"] = public_asset_url(asset)
        payload["media_type"] = "IMAGE" if asset.media_type == "image" else "VIDEO"
    container = provider_response(requests.post(f"{base}/{account.external_id}/threads", data=payload, timeout=120))
    return provider_response(requests.post(f"{base}/{account.external_id}/threads_publish", data={"creation_id": container["id"], "access_token": account.access_token}, timeout=60))


def publish_x(account, post):
    media_ids = []
    for asset in post.assets.all():
        media_response = provider_response(requests.post("https://api.x.com/2/media/upload", json={"media_url": public_asset_url(asset), "media_category": "tweet_video" if asset.media_type == "video" else "tweet_image"}, headers={"Authorization": f"Bearer {account.access_token}"}, timeout=120))
        media_ids.append(media_response.get("data", {}).get("id") or media_response.get("id"))
    payload = {"text": post.body}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    return provider_response(requests.post("https://api.x.com/2/tweets", json=payload, headers={"Authorization": f"Bearer {account.access_token}"}, timeout=60))


def publish_youtube(account, post):
    asset = post.assets.first()
    content_type = mimetypes.guess_type(asset.file.name)[0] or "video/mp4"
    metadata = {"snippet": {"title": post.title, "description": post.body}, "status": {"privacyStatus": account.metadata.get("default_privacy", "private")}}
    headers = {"Authorization": f"Bearer {account.access_token}", "Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": content_type, "X-Upload-Content-Length": str(asset.file.size)}
    start = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", json=metadata, headers=headers, timeout=60)
    provider_response(start)
    upload_url = start.headers.get("Location")
    if not upload_url:
        raise SocialPublishError("YouTube did not return a resumable upload URL.")
    with asset.file.open("rb") as stream:
        uploaded = requests.put(upload_url, data=stream, headers={"Authorization": f"Bearer {account.access_token}", "Content-Type": content_type}, timeout=600)
    return provider_response(uploaded)


PUBLISHERS = {
    SocialAccount.Platform.FACEBOOK: publish_facebook,
    SocialAccount.Platform.INSTAGRAM: publish_instagram,
    SocialAccount.Platform.THREADS: publish_threads,
    SocialAccount.Platform.X: publish_x,
    SocialAccount.Platform.YOUTUBE: publish_youtube,
}


def enqueue_post(post):
    accounts = list(post.accounts.filter(is_active=True))
    if not accounts:
        raise SocialPublishError("Select at least one active social account before queuing.")
    for account in accounts:
        validate_post(post, account)
        SocialDelivery.objects.get_or_create(post=post, account=account, defaults={"next_attempt_at": post.scheduled_at})
    post.status = SocialPost.Status.QUEUED
    post.last_error = ""
    post.save(update_fields=["status", "last_error", "updated_at"])


def process_delivery(delivery_id):
    with transaction.atomic():
        delivery = SocialDelivery.objects.select_for_update().select_related("post", "account").get(pk=delivery_id)
        if delivery.status == SocialDelivery.Status.SUCCESS:
            return delivery
        delivery.status = SocialDelivery.Status.PUBLISHING
        delivery.attempts += 1
        delivery.save(update_fields=["status", "attempts", "updated_at"])
    try:
        validate_post(delivery.post, delivery.account)
        result = PUBLISHERS[delivery.account.platform](delivery.account, delivery.post)
    except Exception as exc:
        delivery.status = SocialDelivery.Status.FAILED
        delivery.error_message = str(exc)[:4000]
        delivery.next_attempt_at = timezone.now() + timedelta(minutes=min(60, 2 ** min(delivery.attempts, 6)))
        delivery.save(update_fields=["status", "error_message", "next_attempt_at", "updated_at"])
        delivery.post.status = SocialPost.Status.FAILED
        delivery.post.last_error = delivery.error_message
        delivery.post.retry_count = delivery.post.retry_count + 1
        delivery.post.save(update_fields=["status", "last_error", "retry_count", "updated_at"])
        return delivery
    delivery.status = SocialDelivery.Status.SUCCESS
    delivery.external_id = str(result.get("id") or result.get("data", {}).get("id", ""))
    delivery.response_payload = result
    delivery.published_at = timezone.now()
    delivery.error_message = ""
    delivery.save(update_fields=["status", "external_id", "response_payload", "published_at", "error_message", "updated_at"])
    refresh_post_status(delivery.post)
    return delivery


def refresh_post_status(post):
    statuses = list(post.deliveries.values_list("status", flat=True))
    if statuses and all(status == SocialDelivery.Status.SUCCESS for status in statuses):
        post.status = SocialPost.Status.PUBLISHED
        post.published_at = timezone.now()
    elif any(status == SocialDelivery.Status.SUCCESS for status in statuses):
        post.status = SocialPost.Status.PARTIAL
    else:
        post.status = SocialPost.Status.FAILED
    post.save(update_fields=["status", "published_at", "updated_at"])
