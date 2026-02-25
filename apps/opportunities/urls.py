from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('', views.OpportunityListView.as_view(), name='list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('<int:pk>/apply/', views.apply_opportunity, name='apply'),
    path('<int:pk>/', views.OpportunityDetailView.as_view(), name='detail'),
    path('<int:pk>/save/', views.save_opportunity, name='save'),
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/<int:pk>/delete/', views.delete_alert, name='delete_alert'),
]
