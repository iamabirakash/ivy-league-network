from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRankSerializer(serializers.ModelSerializer):
    """Serializer for user ranking data"""
    full_name = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'profile_picture_url',
            'university', 'major', 'graduation_year', 'incoscore'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return '/static/images/default-avatar.png'


class UserDetailRankSerializer(serializers.ModelSerializer):
    """Detailed serializer for user ranking with achievement counts"""
    achievements_count = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'profile_picture', 'university', 'major', 'graduation_year',
            'gpa', 'incoscore', 'rank', 'achievements_count'
        ]
    
    def get_achievements_count(self, obj):
        from apps.accounts.models import StudentAchievement
        return StudentAchievement.objects.filter(user=obj, verified=True).count()
    
    def get_rank(self, obj):
        higher_count = User.objects.filter(
            is_active=True,
            incoscore__gt=obj.incoscore
        ).count()
        return higher_count + 1