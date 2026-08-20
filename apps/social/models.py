import base64
import hashlib
from datetime import timedelta

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SocialAccount(models.Model):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook Page"
        INSTAGRAM = "instagram", "Instagram Professional"
        THREADS = "threads", "Threads"
        YOUTUBE = "youtube", "YouTube"
        X = "x", "X / Twitter"

    platform = models.CharField(max_length=20, choices=Platform.choices)
    name = models.CharField(max_length=160)
    external_id = models.CharField(max_length=255)
    access_token_ciphertext = models.TextField()
    refresh_token_ciphertext = models.TextField(blank=True, default="")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    connected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="social_accounts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["platform", "name"]
        constraints = [
            models.UniqueConstraint(fields=["platform", "external_id"], name="unique_social_platform_account"),
        ]

    def __str__(self):
        return f"{self.get_platform_display()} — {self.name}"

    @staticmethod
    def _cipher():
        configured = getattr(settings, "SOCIAL_TOKEN_ENCRYPTION_KEY", "")
        if configured:
            return Fernet(configured.encode())
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    @classmethod
    def encrypt_token(cls, value):
        if not value:
            return ""
        return cls._cipher().encrypt(value.encode()).decode()

    @classmethod
    def decrypt_token(cls, value):
        if not value:
            return ""
        try:
            return cls._cipher().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise ValidationError("The stored social access token cannot be decrypted.") from exc

    @property
    def access_token(self):
        return self.decrypt_token(self.access_token_ciphertext)

    @access_token.setter
    def access_token(self, value):
        self.access_token_ciphertext = self.encrypt_token(value)

    @property
    def refresh_token(self):
        return self.decrypt_token(self.refresh_token_ciphertext)

    @refresh_token.setter
    def refresh_token(self, value):
        self.refresh_token_ciphertext = self.encrypt_token(value)

    @property
    def token_is_expired(self):
        return bool(self.token_expires_at and self.token_expires_at <= timezone.now() + timedelta(minutes=2))


class SocialMediaAsset(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    file = models.FileField(upload_to="social-media/%Y/%m/")
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    alt_text = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="social_media_assets")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name.rsplit("/", 1)[-1]


class SocialPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        QUEUED = "queued", "Queued"
        PUBLISHING = "publishing", "Publishing"
        PUBLISHED = "published", "Published"
        PARTIAL = "partial", "Partially published"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(help_text="Base caption or post text. Platform-specific limits are validated before queuing.")
    link_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="social_posts")
    accounts = models.ManyToManyField(SocialAccount, related_name="posts", blank=True)
    assets = models.ManyToManyField(SocialMediaAsset, related_name="posts", blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or self.body[:60]


class SocialDelivery(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PUBLISHING = "publishing", "Publishing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name="deliveries")
    account = models.ForeignKey(SocialAccount, on_delete=models.PROTECT, related_name="deliveries")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    external_id = models.CharField(max_length=255, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["post", "account"], name="unique_social_delivery"),
        ]

    def __str__(self):
        return f"{self.post} → {self.account} ({self.status})"
