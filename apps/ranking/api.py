from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from .serializers import UserRankSerializer
from .incoscore import InCoScoreCalculator

User = get_user_model()


class RankViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user rankings
    """
    queryset = User.objects.filter(
        is_active=True,
        user_type='student',
        is_superuser=False,
        is_staff=False,
    ).order_by('-incoscore')
    serializer_class = UserRankSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get top 100 users"""
        queryset = self.get_queryset()[:100]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_rank(self, request):
        """Get current user's rank"""
        user = request.user
        
        # Count users with higher score
        higher_count = User.objects.filter(
            is_active=True,
            user_type='student',
            is_superuser=False,
            is_staff=False,
            incoscore__gt=user.incoscore
        ).count()
        
        rank = higher_count + 1
        total_users = User.objects.filter(
            is_active=True,
            user_type='student',
            is_superuser=False,
            is_staff=False,
        ).count()
        
        return Response({
            'rank': rank,
            'total_users': total_users,
            'score': user.incoscore,
            'percentile': round((1 - (rank - 1) / total_users) * 100, 1) if total_users > 0 else 0
        })
    
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Recalculate score for current user"""
        calculator = InCoScoreCalculator()
        new_score = calculator.calculate_score(request.user.id)
        
        return Response({
            'status': 'success',
            'new_score': new_score
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed stats for a user"""
        user = self.get_object()
        
        from apps.accounts.models import StudentAchievement
        
        achievements = StudentAchievement.objects.filter(user=user)
        
        stats = {
            'username': user.username,
            'full_name': user.get_full_name(),
            'incoscore': user.incoscore,
            'achievements': {
                'hackathons': achievements.filter(achievement_type='hackathon').count(),
                'internships': achievements.filter(achievement_type='internship').count(),
                'research': achievements.filter(achievement_type='research').count(),
                'competitions': achievements.filter(achievement_type='competition').count(),
                'certifications': achievements.filter(achievement_type='certification').count(),
                'projects': achievements.filter(achievement_type='project').count(),
            },
            'university': user.university,
            'major': user.major,
            'graduation_year': user.graduation_year,
        }
        
        return Response(stats)


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for leaderboard with different categories
    """
    queryset = User.objects.filter(
        is_active=True,
        user_type='student',
        is_superuser=False,
        is_staff=False,
    )
    serializer_class = UserRankSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_domain(self, request):
        """Get leaderboard filtered by domain"""
        domain = request.query_params.get('domain', '')
        if domain:
            queryset = self.queryset.filter(
                Q(skills__icontains=domain) | 
                Q(interests__icontains=domain)
            ).order_by('-incoscore')[:50]
        else:
            queryset = self.queryset.order_by('-incoscore')[:50]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_university(self, request):
        """Get leaderboard filtered by university"""
        university = request.query_params.get('university', '')
        if university:
            queryset = self.queryset.filter(
                university__icontains=university
            ).order_by('-incoscore')[:50]
        else:
            queryset = self.queryset.order_by('-incoscore')[:50]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_internships(self, request):
        """Get users with most internships"""
        from django.db.models import Count
        from apps.accounts.models import StudentAchievement
        
        users = User.objects.filter(
            is_active=True,
            user_type='student',
            is_superuser=False,
            is_staff=False,
            achievements__achievement_type='internship',
            achievements__verified=True
        ).annotate(
            internship_count=Count('achievements', filter=Q(achievements__achievement_type='internship'))
        ).order_by('-internship_count')[:20]
        
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_research(self, request):
        """Get users with most research papers"""
        from django.db.models import Count
        from apps.accounts.models import StudentAchievement
        
        users = User.objects.filter(
            is_active=True,
            user_type='student',
            is_superuser=False,
            is_staff=False,
            achievements__achievement_type='research',
            achievements__verified=True
        ).annotate(
            research_count=Count('achievements', filter=Q(achievements__achievement_type='research'))
        ).order_by('-research_count')[:20]
        
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
