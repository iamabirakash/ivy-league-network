from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('group/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:pk>/join/', views.join_group, name='join_group'),
    path('group/<int:pk>/leave/', views.leave_group, name='leave_group'),
]