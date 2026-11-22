from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('communities/', views.CommunityListView.as_view(), name='community_list'),
    path('communities/new/', views.CommunityCreateView.as_view(), name='community_create'),
    path('communities/<int:pk>/', views.CommunityDetailView.as_view(), name='community_detail'),
    path('communities/<int:pk>/edit/', views.CommunityUpdateView.as_view(), name='community_update'),
    path('communities/<int:pk>/delete/', views.CommunityDeleteView.as_view(), name='community_delete'),
]