from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .scrapers import ScraperManager
from apps.classification.classifier import OpportunityClassifier
from apps.opportunities.models import Opportunity, UserOpportunity
from apps.accounts.models import User
from apps.notifications.services import NotificationService
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)
BASE_URL = getattr(settings, "BASE_URL", "http://127.0.0.1:8000")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@ivynetwork.local")


@shared_task
def scrape_opportunities_task():
    """Celery task to scrape opportunities"""
    logger.info("Starting opportunity scraping task...")
    
    try:
        manager = ScraperManager()
        new_opportunities = manager.scrape_all()
        
        # Classify new opportunities
        classifier = OpportunityClassifier()
        for opp in new_opportunities:
            classifier.classify_opportunity(opp.id)
        
        # Send notifications for new opportunities
        if new_opportunities:
            send_new_opportunity_notifications([opp.id for opp in new_opportunities])
        
        logger.info(f"Scraping completed. Found {len(new_opportunities)} new opportunities.")
        return len(new_opportunities)
        
    except Exception as e:
        logger.error(f"Scraping task failed: {str(e)}")
        raise


@shared_task
def check_deadlines_task():
    """Check for upcoming deadlines"""
    logger.info("Checking upcoming deadlines...")
    
    upcoming = UserOpportunity.objects.filter(
        status='saved',
        opportunity__deadline__lte=timezone.now() + timezone.timedelta(days=7),
        opportunity__deadline__gt=timezone.now()
    ).select_related('user', 'opportunity')
    
    count = 0
    for item in upcoming:
        send_deadline_reminder(item.user.id, item.opportunity.id)
        count += 1
    
    logger.info(f"Sent {count} deadline reminders")
    return count


@shared_task
def send_deadline_reminder(user_id, opportunity_id):
    """Send deadline reminder email"""
    try:
        user = User.objects.get(id=user_id)
        opportunity = Opportunity.objects.get(id=opportunity_id)
        
        subject = f"Reminder: {opportunity.title} deadline approaching"
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        This is a reminder that the deadline for **{opportunity.title}** at 
        **{opportunity.university.name}** is on **{opportunity.deadline.strftime('%B %d, %Y')}**.
        
        Don't miss this opportunity!
        
        Quick links:
        - View opportunity: {BASE_URL}/opportunities/{opportunity.id}/
        - Apply now: {opportunity.application_url or opportunity.external_url}
        
        Best regards,
        Ivy Opportunity Network Team
        """
        
        send_mail(
            subject,
            message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message.replace('\n', '<br>')
        )
        
        logger.info(f"Sent deadline reminder to {user.email} for {opportunity.title}")
        
    except Exception as e:
        logger.error(f"Failed to send reminder: {str(e)}")


@shared_task
def send_new_opportunity_notifications(opportunity_ids):
    """Send notifications for new opportunities to interested users"""
    from apps.opportunities.models import OpportunityAlert
    
    opportunities = Opportunity.objects.filter(id__in=opportunity_ids)
    
    for opportunity in opportunities:
        # Find users with matching alerts
        alerts = OpportunityAlert.objects.filter(
            is_active=True,
            keywords__icontains=opportunity.title
        ).select_related('user')
        
        for alert in alerts:
            send_opportunity_alert(alert.user.id, opportunity.id)


@shared_task
def send_opportunity_alert(user_id, opportunity_id):
    """Send opportunity alert to user"""
    try:
        user = User.objects.get(id=user_id)
        opportunity = Opportunity.objects.get(id=opportunity_id)
        
        subject = f"New Opportunity: {opportunity.title}"
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        A new opportunity matching your interests has been posted:
        
        **{opportunity.title}**
        **University:** {opportunity.university.name}
        **Deadline:** {opportunity.deadline.strftime('%B %d, %Y')}
        
        {opportunity.description[:200]}...
        
        View opportunity: {BASE_URL}/opportunities/{opportunity.id}/
        
        Best regards,
        Ivy Opportunity Network Team
        """
        
        send_mail(
            subject,
            message,
            DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message.replace('\n', '<br>')
        )
        
        logger.info(f"Sent opportunity alert to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send alert: {str(e)}")


@shared_task
def cleanup_old_opportunities():
    """Deactivate expired opportunities"""
    expired = Opportunity.objects.filter(
        deadline__lt=timezone.now(),
        is_active=True
    )
    
    count = expired.update(is_active=False)
    logger.info(f"Deactivated {count} expired opportunities")
    return count
