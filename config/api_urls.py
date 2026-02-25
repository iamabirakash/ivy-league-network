from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.opportunities.api import OpportunityViewSet, UserOpportunityViewSet
from apps.community.api import PostViewSet, CommentViewSet, GroupViewSet
from apps.ranking.api import RankViewSet

router = DefaultRouter()
router.register(r'opportunities', OpportunityViewSet)
router.register(r'user-opportunities', UserOpportunityViewSet, basename='user-opportunities')
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'ranking', RankViewSet, basename='ranking')

urlpatterns = [
    path('', include(router.urls)),
]
