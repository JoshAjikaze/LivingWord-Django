from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(ModelAdmin):
    list_display = ("email", "subscribed_at", "is_active")
    list_editable = ("is_active",)
    search_fields = ("email",)
    readonly_fields = ("subscribed_at",)
