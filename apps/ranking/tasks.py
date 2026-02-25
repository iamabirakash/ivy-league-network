from celery import shared_task
from django.contrib.auth import get_user_model
from .incoscore import InCoScoreCalculator
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def update_user_ranking_task(user_id):
    """Update ranking for a single user"""
    calculator = InCoScoreCalculator()
    score = calculator.calculate_score(user_id)
    logger.info(f"Updated ranking for user {user_id}: {score}")
    return score


@shared_task
def update_all_rankings_task():
    """Update rankings for all users"""
    users = User.objects.filter(is_active=True)
    calculator = InCoScoreCalculator()
    
    count = 0
    for user in users:
        calculator.calculate_score(user.id)
        count += 1
    
    logger.info(f"Updated rankings for {count} users")
    return count


@shared_task
def recalculate_rankings_for_achievement(achievement_id):
    """Recalculate rankings when an achievement is added/verified"""
    from apps.accounts.models import StudentAchievement
    
    try:
        achievement = StudentAchievement.objects.get(id=achievement_id)
        calculator = InCoScoreCalculator()
        calculator.calculate_score(achievement.user.id)
        logger.info(f"Recalculated ranking for user {achievement.user.id} due to achievement {achievement_id}")
    except Exception as e:
        logger.error(f"Error recalculating ranking for achievement {achievement_id}: {str(e)}")