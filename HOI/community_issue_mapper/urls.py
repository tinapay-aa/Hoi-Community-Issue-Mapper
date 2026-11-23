from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('communities/', views.CommunityListView.as_view(), name='community_list'),
    path('communities/new/', views.CommunityCreateView.as_view(), name='community_create'),
    path('communities/<int:pk>/', views.CommunityDetailView.as_view(), name='community_detail'),
    path('communities/<int:pk>/edit/', views.CommunityUpdateView.as_view(), name='community_update'),
    path('communities/<int:pk>/delete/', views.CommunityDeleteView.as_view(), name='community_delete'),
    
    path('issues/new/', views.issue_create, name='issue_create'),
    path('issues/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:pk>/edit/', views.issue_update, name='issue_update'),
    path('issues/<int:pk>/delete/', views.issue_delete, name='issue_delete'),
    path('issues/<int:pk>/status/', views.issue_status, name='issue_status'),
    
    path('issues/<int:issue_id>/comments/create/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/update/', views.comment_update, name='comment_update'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    
    path('settings/', views.profile_settings, name='profile_settings'),
]