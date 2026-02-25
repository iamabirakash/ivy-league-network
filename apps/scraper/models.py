from django.db import models
from django.utils import timezone


class ScraperRun(models.Model):
    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    university = models.ForeignKey('opportunities.University', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    opportunities_found = models.IntegerField(default=0)
    opportunities_created = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Scraper run at {self.started_at}"


class Source(models.Model):
    SOURCE_TYPES = (
        ("platform", "Platform"),
        ("portal", "University Portal"),
        ("api", "API"),
    )

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    base_url = models.URLField()
    listing_url = models.URLField()
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default="platform")
    university = models.ForeignKey(
        "opportunities.University",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_sources",
    )
    active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
