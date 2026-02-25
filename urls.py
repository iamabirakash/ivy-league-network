from django.urls import path
from . import views

app_name = 'ranking'

urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='leaderboard'),
    path('my-rank/', views.my_rank, name='my_rank'),
]