from django.contrib import admin
from .models import ScraperRun, Source


@admin.register(ScraperRun)
class ScraperRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "university",
        "status",
        "opportunities_found",
        "opportunities_created",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "started_at")
    search_fields = ("university__name", "error_message")


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "source_type", "active", "university", "last_scraped")
    list_filter = ("source_type", "active")
    search_fields = ("name", "code", "base_url", "listing_url")
