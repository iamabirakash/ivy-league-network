from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentAchievement, UserFollow


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'incoscore', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {
            'fields': (
                'user_type', 'profile_picture', 'bio', 'university', 
                'graduation_year', 'major', 'gpa', 'skills', 'interests',
                'resume', 'linkedin_url', 'github_url', 'portfolio_url', 'incoscore'
            )
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'university')
    ordering = ('-incoscore',)


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'achievement_type', 'organization', 'date_achieved', 'verified')
    list_filter = ('achievement_type', 'verified')
    search_fields = ('user__username', 'title', 'organization')
    date_hierarchy = 'date_achieved'
    actions = ['verify_achievements']
    
    def verify_achievements(self, request, queryset):
        queryset.update(verified=True, verified_by=request.user)
        # Recalculate scores for affected users
        from apps.ranking.tasks import recalculate_rankings_for_achievement
        for achievement in queryset:
            recalculate_rankings_for_achievement.delay(achievement.id)
        self.message_user(request, f"{queryset.count()} achievements verified.")
    verify_achievements.short_description = "Verify selected achievements"


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    date_hierarchy = 'created_at'