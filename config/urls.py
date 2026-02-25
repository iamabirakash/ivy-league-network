from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('apps.accounts.urls')),
    path('opportunities/', include('apps.opportunities.urls')),
    path('community/', include('apps.community.urls')),  # Add this line
    path('ranking/', include('apps.ranking.urls')),
    path('classification/', include('apps.classification.urls')),
    path('api/', include('config.api_urls')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
