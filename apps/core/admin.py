from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import AuthorProfile, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """Singleton admin — hides the 'add' action once a row exists."""

    fieldsets = (
        (None, {"fields": ("imprint_name", "tagline", "hero_image")}),
        ("Homepage copy", {"fields": ("intro_text", "mission_text")}),
        ("Footer", {"fields": ("footer_blurb",)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuthorProfile)
class AuthorProfileAdmin(ModelAdmin):
    list_display = ("name",)

    def has_add_permission(self, request):
        return not AuthorProfile.objects.exists()
