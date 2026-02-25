import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from apps.opportunities.models import OpportunityAlert

logger = logging.getLogger(__name__)
User = get_user_model()
BASE_URL = getattr(settings, "BASE_URL", "http://127.0.0.1:8000")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@ivynetwork.local")


class NotificationService:
    """Service for handling opportunity/deadline notifications."""

    @staticmethod
    def notify_new_opportunities(opportunities):
        if not opportunities:
            return

        for opportunity in opportunities:
            alerts = OpportunityAlert.objects.filter(is_active=True).select_related("user")
            for alert in alerts:
                if NotificationService._matches_alert(opportunity, alert):
                    NotificationService._send_opportunity_email(alert.user, opportunity)

    @staticmethod
    def _matches_alert(opportunity, alert):
        if alert.keywords:
            keywords = alert.keywords.lower().split()
            text = f"{opportunity.title} {opportunity.description}".lower()
            if not any(keyword in text for keyword in keywords):
                return False

        if alert.domains and opportunity.domain not in alert.domains:
            return False

        if alert.opportunity_types and opportunity.opportunity_type not in alert.opportunity_types:
            return False

        if alert.universities and str(opportunity.university_id) not in alert.universities:
            return False

        return True

    @staticmethod
    def _send_opportunity_email(user, opportunity):
        subject = f"New Opportunity: {opportunity.title}"
        message = f"""
Hi {user.get_full_name() or user.username},

A new opportunity matching your interests has been posted:

Title: {opportunity.title}
University: {opportunity.university.name}
Deadline: {opportunity.deadline.strftime('%B %d, %Y')}

{opportunity.description[:200]}...

View it here: {BASE_URL}/opportunities/{opportunity.id}/
"""
        try:
            send_mail(subject, message, DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            logger.info("Sent opportunity notification to %s", user.email)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", user.email, exc)

    @staticmethod
    def send_deadline_reminder(user_opportunity):
        subject = f"Reminder: {user_opportunity.opportunity.title} deadline approaching"
        message = f"""
Hi {user_opportunity.user.get_full_name() or user_opportunity.user.username},

This is a reminder that the deadline for {user_opportunity.opportunity.title}
at {user_opportunity.opportunity.university.name} is approaching.

Deadline: {user_opportunity.opportunity.deadline.strftime('%B %d, %Y')}
Apply here: {user_opportunity.opportunity.application_url or user_opportunity.opportunity.external_url}
"""
        try:
            send_mail(
                subject,
                message,
                DEFAULT_FROM_EMAIL,
                [user_opportunity.user.email],
                fail_silently=False,
            )
            logger.info("Sent deadline reminder to %s", user_opportunity.user.email)
        except Exception as exc:
            logger.error("Failed to send reminder: %s", exc)
