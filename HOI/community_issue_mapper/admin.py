from django.contrib import admin
from .models import Category, Issue, IssueUpdate


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


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


@admin.register(IssueUpdate)
class IssueUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'issue',
        'updated_by',
        'previous_status',
        'new_status',
        'created_at'
    )