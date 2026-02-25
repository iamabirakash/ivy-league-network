from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Opportunity, UserOpportunity
from .serializers import OpportunitySerializer, UserOpportunitySerializer
from apps.accounts.models import User
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.filter(is_active=True, deadline__gte=timezone.now())
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['domain', 'opportunity_type', 'university', 'is_remote', 'is_paid']
    search_fields = ['title', 'description', 'university__name']
    ordering_fields = ['deadline', 'created_at', 'views_count']
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        opportunity = self.get_object()
        user_opp, created = UserOpportunity.objects.get_or_create(
            user=request.user,
            opportunity=opportunity,
            defaults={'status': 'saved'}
        )
        
        if not created and user_opp.status == 'saved':
            user_opp.delete()
            return Response({'status': 'unsaved'})
        elif not created:
            user_opp.status = 'saved'
            user_opp.save()
            return Response({'status': 'saved'})
        else:
            opportunity.saved_count += 1
            opportunity.save()
            return Response({'status': 'saved'})
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended opportunities based on user interests"""
        user = request.user
        opportunities = self.get_queryset()
        filters = Q()
        for token in (user.interests or []):
            token = str(token).strip().lower()
            if token:
                filters |= Q(domain=token) | Q(tags__icontains=token) | Q(title__icontains=token)
        for token in (user.skills or []):
            token = str(token).strip().lower()
            if token:
                filters |= Q(description__icontains=token) | Q(tags__icontains=token)
        if filters:
            opportunities = opportunities.filter(filters)
        opportunities = opportunities.order_by("-is_featured", "deadline", "-created_at")[:10]
        
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        opportunity = self.get_object()
        submitted_data = request.data.get("submitted_data", {}) or {}
        user_opp, _ = UserOpportunity.objects.get_or_create(
            user=request.user,
            opportunity=opportunity,
            defaults={"status": "applied", "application_data": submitted_data, "applied_date": timezone.now()},
        )
        if user_opp.status != "applied":
            user_opp.status = "applied"
        user_opp.applied_date = timezone.now()
        user_opp.application_data = submitted_data
        user_opp.save()

        opportunity.applications_count += 1
        opportunity.save(update_fields=["applications_count"])

        return Response({"status": "applied"})

    @action(detail=True, methods=["get"])
    def recommended_students(self, request, pk=None):
        opportunity = self.get_object()
        profile_filter = Q()
        terms = []
        if opportunity.domain:
            terms.append(opportunity.domain)
        terms.extend([str(tag).strip().lower() for tag in (opportunity.tags or []) if str(tag).strip()])
        for term in terms:
            profile_filter |= Q(interests__icontains=term) | Q(skills__icontains=term)

        users = User.objects.filter(is_active=True, user_type="student")
        if profile_filter:
            users = users.filter(profile_filter)
        users = users.order_by("-incoscore")[:10]

        data = [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name() or user.username,
                "incoscore": user.incoscore,
            }
            for user in users
        ]
        return Response(data)


class UserOpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = UserOpportunitySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return UserOpportunity.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        queryset = self.get_queryset().filter(status='saved')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def applied(self, request):
        queryset = self.get_queryset().filter(status='applied')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
