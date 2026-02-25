from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# This file is intentionally left with basic signals
# You can add signal handlers here when needed

@receiver(post_save, sender='scraper.ScraperRun')
def clear_scraper_cache(sender, **kwargs):
    """Clear cache when new scrapes happen"""
    cache.delete('recent_opportunities')
    cache.delete('university_stats')
    logger.info("Cleared scraper-related cache")

# Keep cache hot by invalidating summaries after each scraper run.
