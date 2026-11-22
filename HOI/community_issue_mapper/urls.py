from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('settings/', views.profile_settings, name='profile_settings'),
]