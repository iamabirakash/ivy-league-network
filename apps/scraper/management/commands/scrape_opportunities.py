from django.core.management.base import BaseCommand
from apps.scraper.tasks import scrape_opportunities_task
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the opportunity scraping task (development friendly).'

    def handle(self, *args, **options):
        self.stdout.write('Starting opportunity scraping...')
        try:
            # Call task synchronously (Celery is eager in dev by default)
            result = scrape_opportunities_task()
            self.stdout.write(self.style.SUCCESS(f'Scraping finished. Result: {result}'))
        except Exception as e:
            logger.exception('Scraping command failed: %s', e)
            self.stdout.write(self.style.ERROR(f'Scraping failed: {e}'))
