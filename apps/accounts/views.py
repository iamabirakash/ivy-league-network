from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from .models import User, StudentAchievement, UserFollow
from .forms import CustomUserCreationForm, UserProfileForm, StudentAchievementForm
from apps.ranking.incoscore import InCoScoreCalculator


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    achievements = StudentAchievement.objects.filter(user=request.user)
    followers_count = UserFollow.objects.filter(following=request.user).count()
    following_count = UserFollow.objects.filter(follower=request.user).count()
    
    # Get recent followers
    recent_followers = UserFollow.objects.filter(
        following=request.user
    ).select_related('follower').order_by('-created_at')[:5]
    
    context = {
        'achievements': achievements,
        'followers_count': followers_count,
        'following_count': following_count,
        'recent_followers': recent_followers,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['achievements'] = StudentAchievement.objects.filter(user=user, verified=True)
        context['is_following'] = UserFollow.objects.filter(
            follower=self.request.user, 
            following=user
        ).exists()
        context['followers_count'] = UserFollow.objects.filter(following=user).count()
        context['following_count'] = UserFollow.objects.filter(follower=user).count()
        
        # Check if it's the current user's profile
        context['is_own_profile'] = (self.request.user == user)
        
        return context


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).order_by('-incoscore')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(university__icontains=search_query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


@login_required
def add_achievement(request):
    if request.method == 'POST':
        form = StudentAchievementForm(request.POST, request.FILES)
        if form.is_valid():
            achievement = form.save(commit=False)
            achievement.user = request.user
            achievement.save()
            
            # Recalculate user's InCoScore
            calculator = InCoScoreCalculator()
            calculator.calculate_score(request.user.id)
            
            messages.success(request, 'Achievement added successfully!')
            return redirect('accounts:profile')
    else:
        form = StudentAchievementForm()
    return render(request, 'accounts/add_achievement.html', {'form': form})


@login_required
def delete_achievement(request, pk):
    achievement = get_object_or_404(StudentAchievement, pk=pk, user=request.user)
    achievement.delete()
    
    # Recalculate user's InCoScore
    calculator = InCoScoreCalculator()
    calculator.calculate_score(request.user.id)
    
    messages.success(request, 'Achievement deleted successfully!')
    return redirect('accounts:profile')


@login_required
def follow_user(request, user_id):
    """Follow a user"""
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if request.user == user_to_follow:
        messages.error(request, "You cannot follow yourself.")
        return redirect('accounts:user_detail', username=user_to_follow.username)
    
    follow, created = UserFollow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if created:
        messages.success(request, f'You are now following {user_to_follow.get_full_name() or user_to_follow.username}')
        
        # Create notification (if you have notifications)
        # notify.send(request.user, recipient=user_to_follow, verb='started following you')
    else:
        messages.info(request, f'You already follow {user_to_follow.get_full_name() or user_to_follow.username}')
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': 'follow',
            'following': True,
            'followers_count': UserFollow.objects.filter(following=user_to_follow).count()
        })
    
    return redirect('accounts:user_detail', username=user_to_follow.username)


@login_required
def unfollow_user(request, user_id):
    """Unfollow a user"""
    user_to_unfollow = get_object_or_404(User, id=user_id)
    
    deleted_count = UserFollow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()[0]
    
    if deleted_count > 0:
        messages.success(request, f'You have unfollowed {user_to_unfollow.get_full_name() or user_to_unfollow.username}')
    else:
        messages.info(request, f'You were not following {user_to_unfollow.get_full_name() or user_to_unfollow.username}')
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': 'unfollow',
            'following': False,
            'followers_count': UserFollow.objects.filter(following=user_to_unfollow).count()
        })
    
    return redirect('accounts:user_detail', username=user_to_unfollow.username)


@login_required
def followers_list(request, username):
    """View list of followers for a user"""
    user = get_object_or_404(User, username=username)
    followers = UserFollow.objects.filter(following=user).select_related('follower')
    
    context = {
        'profile_user': user,
        'followers': followers,
        'count': followers.count()
    }
    return render(request, 'accounts/followers_list.html', context)


@login_required
def following_list(request, username):
    """View list of users that a user is following"""
    user = get_object_or_404(User, username=username)
    following = UserFollow.objects.filter(follower=user).select_related('following')
    
    context = {
        'profile_user': user,
        'following': following,
        'count': following.count()
    }
    return render(request, 'accounts/following_list.html', context)