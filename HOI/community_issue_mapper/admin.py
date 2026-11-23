from django.contrib import admin
from .models import Category, Community, CommunityMembership, Issue, IssueComment, IssueImage, IssueUpdate, Location

admin.site.register(Community)
admin.site.register(CommunityMembership)
admin.site.register(Location)
admin.site.register(IssueImage)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'reported_by',
        'status',
        'priority',
        'created_at'
    )

    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description', 'address')
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(IssueUpdate)
class IssueUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'issue',
        'updated_by',
        'previous_status',
        'new_status',
        'created_at'
    )

    list_filter = ('new_status', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 20

@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ('issue', 'author', 'created_at')
    search_fields = ('body', 'author__username', 'issue__title')
    ordering = ('-created_at',)
    list_per_page = 20