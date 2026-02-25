from django.urls import path

from . import views

app_name = "classification"

urlpatterns = [
    path("opportunity/<int:pk>/", views.classify_opportunity, name="classify_opportunity"),
    path("pending/", views.classify_pending, name="classify_pending"),
]
