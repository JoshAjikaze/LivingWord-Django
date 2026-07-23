from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import ModelAdmin, TabularInline

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
        "status",
        "price",
        "discount_percent",
        "discount_is_active",
        "published_at",
    )
    list_editable = ("status", "discount_percent")
    list_filter = ("status",)
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BuyLinkInline]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("title", "slug", "author_name", "status", "published_at")}),
        ("Cover & content", {
            "fields": ("cover_image", "short_description", "description", "whats_inside", "sample_excerpt")
        }),
        ("Pricing & discount", {
            "fields": ("price", "discount_percent", "discount_active_until"),
            "description": "Discount applies automatically while 'discount active until' is in the future.",
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
