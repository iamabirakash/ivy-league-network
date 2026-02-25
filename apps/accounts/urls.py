from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='user_detail'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    
    # Achievements
    path('achievements/add/', views.add_achievement, name='add_achievement'),
    path('achievements/<int:pk>/delete/', views.delete_achievement, name='delete_achievement'),
    
    # Follow/Unfollow
    path('follow/<int:user_id>/', views.follow_user, name='follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow'),
    path('<str:username>/followers/', views.followers_list, name='followers'),
    path('<str:username>/following/', views.following_list, name='following'),
]