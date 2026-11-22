from django.db.models import Q
from django.shortcuts import render

from .models import Category, Community, Issue

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import CommunityForm
from .models import Category, Community, CommunityMembership, Issue


def home(request):
    communities = Community.objects.filter(is_active=True)
    categories = Category.objects.all()

    issues = (
        Issue.objects
        .select_related('category', 'community', 'reported_by', 'location')
        .prefetch_related('images')
    )

    # Filter: community (sidebar)
    active_community = None
    community_id = request.GET.get('community')
    if community_id and community_id.isdigit():
        active_community = communities.filter(pk=community_id).first()
        if active_community:
            issues = issues.filter(community=active_community)

    # Filter: only issues reported by the logged-in user (sidebar)
    only_mine = request.GET.get('mine') == '1' and request.user.is_authenticated
    if only_mine:
        issues = issues.filter(reported_by=request.user)

    # Filter: search box (sidebar)
    q = request.GET.get('q', '').strip()
    if q:
        issues = issues.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(location__address__icontains=q)
        )

    # Plain dicts so the template can hand them to Leaflet via json_script
    issues_data = [
        {
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'status': issue.status,
            'priority': issue.priority,
            'category': issue.category.name,
            'community': issue.community.name,
            'reported_by': issue.reported_by.username,
            'created_at': issue.created_at.strftime('%b %d, %Y'),
            'latitude': float(issue.location.latitude),
            'longitude': float(issue.location.longitude),
            'address': issue.location.address,
            'images': [
                {'url': img.image.url, 'type': img.image_type}
                for img in issue.images.all()
            ],
            'comments': [],  # TODO: fill in once an IssueComment model exists
        }
        for issue in issues
    ]

    return render(request, 'home.html', {
        'communities': communities,
        'categories': categories,
        'active_community': active_community,
        'only_mine': only_mine,
        'q': q,
        'issues': issues_data,
    })


class CommunityListView(ListView):
    template_name = 'communities/list.html'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Community.objects.filter(is_active=True)
            .annotate(
                issue_count=Count('issues', distinct=True),
                member_count=Count('memberships', distinct=True),
            )
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs


class CommunityDetailView(DetailView):
    model = Community
    template_name = 'communities/detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Archived communities are only visible to their managers
        if not obj.is_active and not obj.can_be_managed_by(self.request.user):
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        community = self.object
        ctx['can_manage'] = community.can_be_managed_by(self.request.user)
        ctx['recent_issues'] = community.issues.select_related('category')[:5]
        ctx['issue_count'] = community.issues.count()
        ctx['member_count'] = community.memberships.count()
        return ctx


class CommunityCreateView(LoginRequiredMixin, CreateView):
    model = Community
    form_class = CommunityForm
    template_name = 'communities/form.html'

    @transaction.atomic
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        CommunityMembership.objects.create(
            community=self.object, user=self.request.user, role='Admin'
        )
        messages.success(self.request, f'“{self.object.name}” was created.')
        return response

    def get_success_url(self):
        return reverse('community_detail', args=[self.object.pk])


class CommunityManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only people who can manage the community may continue."""
    model = Community

    def test_func(self):
        return self.get_object().can_be_managed_by(self.request.user)


class CommunityUpdateView(CommunityManagerMixin, UpdateView):
    form_class = CommunityForm
    template_name = 'communities/form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Community updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('community_detail', args=[self.object.pk])


class CommunityDeleteView(CommunityManagerMixin, DeleteView):
    template_name = 'communities/confirm_delete.html'
    success_url = reverse_lazy('community_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['issue_count'] = self.object.issues.count()
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'“{self.object.name}” was deleted.')
        return super().form_valid(form)