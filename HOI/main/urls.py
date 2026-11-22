from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('community_issue_mapper.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('community_issue_mapper.urls')),
]

