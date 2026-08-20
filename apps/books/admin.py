from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Book, BuyLink


class BuyLinkInline(TabularInline):
    model = BuyLink
    extra = 1
    fields = ("platform", "url", "order")


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = (
        "cover_thumb",
        "title",
        "isbn",
        "status",
        "price",
        "discount_percent",
        "discount_is_active",
        "has_ebook",
        "has_qr_code",
        "published_at",
    )
    list_editable = ("status", "discount_percent")
    list_filter = ("status", "published_at")
    search_fields = ("title", "isbn", "author_name", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BuyLinkInline]
    readonly_fields = (
        "created_at",
        "updated_at",
        "cover_preview",
        "ebook_download",
        "sample_download",
        "qr_preview",
        "qr_target",
        "qr_download",
    )

    fieldsets = (
        ("Book identity", {
            "fields": ("title", "slug", "author_name", "isbn", "status", "published_at"),
        }),
        ("Cover & content", {
            "fields": (
                "cover_image",
                "cover_preview",
                "short_description",
                "description",
                "whats_inside",
            ),
        }),
        ("Files", {
            "description": "Upload the full paid ebook and an optional public excerpt. PDF and EPUB files are accepted.",
            "fields": ("ebook_file", "ebook_download", "sample_excerpt", "sample_download"),
        }),
        ("QR code", {
            "description": "Automatically regenerated on every save. Set PUBLIC_SITE_URL to the deployed HTTPS domain in production.",
            "fields": ("qr_preview", "qr_target", "qr_download"),
        }),
        ("Pricing & external store", {
            "fields": ("price", "discount_percent", "discount_active_until", "amazon_store_url"),
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Cover")
    def cover_thumb(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;" />', obj.cover_image.url)
        return "—"

    @admin.display(boolean=True, description="Discount active")
    def discount_is_active(self, obj):
        return obj.discount_is_active

    @admin.display(boolean=True, description="Ebook uploaded")
    def has_ebook(self, obj):
        return bool(obj.ebook_file)

    @admin.display(boolean=True, description="QR generated")
    def has_qr_code(self, obj):
        return bool(obj.qr_code)

    @admin.display(description="Cover preview")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "No cover uploaded."
        return format_html(
            '<img src="{}" style="max-height:220px;max-width:160px;border-radius:6px;" />',
            obj.cover_image.url,
        )

    @admin.display(description="Full ebook")
    def ebook_download(self, obj):
        if not obj.ebook_file:
            return "No full ebook uploaded."
        return format_html('<a href="{}" target="_blank">Open uploaded ebook</a>', obj.ebook_file.url)

    @admin.display(description="Sample excerpt")
    def sample_download(self, obj):
        if not obj.sample_excerpt:
            return "No sample excerpt uploaded."
        return format_html('<a href="{}" target="_blank">Open uploaded excerpt</a>', obj.sample_excerpt.url)

    @admin.display(description="QR preview")
    def qr_preview(self, obj):
        if not obj.qr_code:
            return "QR code will be generated after the book is saved."
        return format_html(
            '<img src="{}" alt="QR code for {}" style="width:220px;height:220px;image-rendering:pixelated;" />',
            obj.qr_code.url,
            obj.title,
        )

    @admin.display(description="QR target URL")
    def qr_target(self, obj):
        if not obj.pk:
            return "Save the book first to generate its public URL."
        return format_html('<a href="{}" target="_blank">{}</a>', obj.qr_target_url, obj.qr_target_url)

    @admin.display(description="Download QR code")
    def qr_download(self, obj):
        if not obj.qr_code:
            return "No QR code generated yet."
        return format_html(
            '<a href="{}" download="book-{}-qr.png" target="_blank">Download PNG</a>',
            obj.qr_code.url,
            obj.pk,
        )
