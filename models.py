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