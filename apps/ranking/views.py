from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class LeaderboardView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'ranking/leaderboard.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = User.objects.filter(
            is_active=True,
            user_type='student',
            is_superuser=False,
            is_staff=False,
        ).order_by('-incoscore')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top_three'] = self.get_queryset()[:3]
        return context


def my_rank(request):
    user_rank = User.objects.filter(
        is_active=True,
        user_type='student',
        is_superuser=False,
        is_staff=False,
        incoscore__gt=request.user.incoscore
    ).count() + 1
    
    total_users = User.objects.filter(
        is_active=True,
        user_type='student',
        is_superuser=False,
        is_staff=False,
    ).count()
    
    context = {
        'rank': user_rank,
        'total_users': total_users,
        'percentile': round((1 - (user_rank - 1) / total_users) * 100, 1) if total_users > 0 else 0
    }
    return render(request, 'ranking/my_rank.html', context)
