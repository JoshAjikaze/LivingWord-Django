from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path

from .models import SocialAccount, SocialDelivery, SocialMediaAsset, SocialPost
from .services import SocialPublishError, enqueue_post, process_delivery


@admin.register(SocialAccount)
class SocialAccountAdmin(ModelAdmin):
    change_list_template = "admin/social/socialaccount/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("connect/<str:platform>/", self.admin_site.admin_view(self.connect_view), name="social_socialaccount_connect"),
        ]
        return custom_urls + urls

    def connect_view(self, request, platform):
        return redirect("social:oauth_start", platform=platform)

    list_display = ("name", "platform", "external_id", "is_active", "token_expires_at", "updated_at")
    list_filter = ("platform", "is_active")
    search_fields = ("name", "external_id")
    readonly_fields = ("access_token_ciphertext", "refresh_token_ciphertext", "created_at", "updated_at")


@admin.register(SocialMediaAsset)
class SocialMediaAssetAdmin(ModelAdmin):
    list_display = ("file", "media_type", "created_by", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("file", "alt_text")


class SocialDeliveryInline(TabularInline):
    model = SocialDelivery
    extra = 0
    can_delete = False
    readonly_fields = ("account", "status", "external_id", "response_payload", "error_message", "attempts", "published_at")


@admin.action(description="Queue selected posts for publishing")
def queue_posts(modeladmin, request, queryset):
    queued = 0
    for post in queryset:
        try:
            enqueue_post(post)
            queued += 1
        except SocialPublishError as exc:
            messages.error(request, f"{post}: {exc}")
    if queued:
        messages.success(request, f"Queued {queued} post(s). Run process_social_queue to publish them.")


@admin.action(description="Retry selected failed deliveries now")
def retry_deliveries(modeladmin, request, queryset):
    retried = 0
    for delivery in queryset.filter(status=SocialDelivery.Status.FAILED):
        delivery.next_attempt_at = None
        delivery.status = SocialDelivery.Status.QUEUED
        delivery.save(update_fields=["next_attempt_at", "status", "updated_at"])
        retried += 1
    messages.success(request, f"Queued {retried} failed delivery(ies) for retry.")


@admin.register(SocialPost)
class SocialPostAdmin(ModelAdmin):
    list_display = ("__str__", "status", "scheduled_at", "created_by", "created_at")
    list_filter = ("status", "scheduled_at", "created_at")
    search_fields = ("title", "body", "last_error")
    filter_horizontal = ("accounts", "assets")
    readonly_fields = ("published_at", "retry_count", "last_error", "created_at", "updated_at")
    inlines = (SocialDeliveryInline,)
    actions = (queue_posts,)


@admin.register(SocialDelivery)
class SocialDeliveryAdmin(ModelAdmin):
    list_display = ("post", "account", "status", "attempts", "published_at", "updated_at")
    list_filter = ("status", "account__platform", "published_at")
    search_fields = ("post__title", "account__name", "external_id", "error_message")
    readonly_fields = [field.name for field in SocialDelivery._meta.fields]
    actions = (retry_deliveries,)
