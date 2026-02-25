from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.community.models import Post


class CommunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="charlie",
            email="charlie@example.com",
            password="pass12345",
            user_type="student",
        )

    def test_create_post(self):
        self.client.login(username="charlie", password="pass12345")
        response = self.client.post(
            reverse("community:create_post"),
            {"title": "Hello", "content": "First post"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)
