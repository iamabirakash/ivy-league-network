from django.test import TestCase

from apps.accounts.models import User, StudentAchievement
from apps.ranking.incoscore import InCoScoreCalculator


class InCoScoreTests(TestCase):
    def test_calculate_score_updates_user(self):
        user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="pass12345",
            gpa=3.8,
            user_type="student",
        )
        StudentAchievement.objects.create(
            user=user,
            achievement_type="project",
            title="AI Platform",
            description="Built a scalable machine learning pipeline project with deep learning.",
            organization="University Lab",
            date_achieved="2025-01-15",
            verified=True,
        )

        score = InCoScoreCalculator().calculate_score(user.id)
        user.refresh_from_db()

        self.assertGreaterEqual(score, 0)
        self.assertEqual(user.incoscore, score)
