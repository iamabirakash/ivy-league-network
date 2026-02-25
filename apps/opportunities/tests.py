from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.opportunities.models import University, Opportunity, UserOpportunity, Application


class OpportunityFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pass12345",
            interests=["ai"],
            skills=["python", "nlp"],
            user_type="student",
        )
        self.university = University.objects.create(
            name="Harvard University",
            code="harvard",
            website="https://harvard.edu",
            opportunities_url="https://harvard.edu/opportunities",
        )
        self.opportunity = Opportunity.objects.create(
            title="AI Research Internship",
            description="Great opportunity for AI and NLP students.",
            opportunity_type="internship",
            domain="ai",
            university=self.university,
            external_url="https://harvard.edu/opportunity/1",
            deadline=timezone.now() + timezone.timedelta(days=10),
            source_url="https://harvard.edu/opportunity/1",
            tags=["ai", "nlp"],
        )

    def test_save_and_unsave_opportunity(self):
        self.client.login(username="alice", password="pass12345")

        save_url = reverse("opportunities:save", kwargs={"pk": self.opportunity.id})
        self.client.get(save_url)
        self.assertTrue(
            UserOpportunity.objects.filter(user=self.user, opportunity=self.opportunity, status="saved").exists()
        )

        self.client.get(save_url)
        self.assertFalse(
            UserOpportunity.objects.filter(user=self.user, opportunity=self.opportunity, status="saved").exists()
        )

    def test_apply_opportunity_creates_records(self):
        self.client.login(username="alice", password="pass12345")
        apply_url = reverse("opportunities:apply", kwargs={"pk": self.opportunity.id})

        resume = SimpleUploadedFile("resume.txt", b"My resume data")
        response = self.client.post(
            apply_url,
            data={
                "resume_used": resume,
                "submitted_data": '{"motivation":"I am excited to apply."}',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Application.objects.filter(user=self.user, opportunity=self.opportunity).count(), 1)
        user_opp = UserOpportunity.objects.get(user=self.user, opportunity=self.opportunity)
        self.assertEqual(user_opp.status, "applied")
