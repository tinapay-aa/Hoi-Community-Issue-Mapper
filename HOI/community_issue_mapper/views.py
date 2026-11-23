from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import CommunityForm, IssueCommentForm, IssueForm, IssueStatusForm, ProfileForm, UserForm
from .models import (
    Category, Community, CommunityMembership, Issue,
    IssueComment, IssueImage, IssueUpdate, Profile
)

MANAGER_ROLES = ('Moderator', 'Admin')


# ---------- Permission helpers ----------
def managed_community_ids(user):
    """Communities this user moderates/admins/created."""
    if not user.is_authenticated:
        return set()
    member = CommunityMembership.objects.filter(user=user, role__in=MANAGER_ROLES)
    created = Community.objects.filter(created_by=user)
    return set(member.values_list('community_id', flat=True)) | set(created.values_list('id', flat=True))


def is_manager(user, issue):
    return user.is_authenticated and (user.is_staff or issue.community_id in managed_community_ids(user))


def is_owner(user, issue):
    return user.is_authenticated and issue.reported_by_id == user.id


def can_edit(user, issue):
    return is_owner(user, issue) or is_manager(user, issue)


# ---------- Comment helpers ----------
def serialize_comment(comment, user):
    is_author = user.is_authenticated and comment.author_id == user.id
    return {
        'id': comment.id,
        'author': comment.author.username,
        'body': comment.body,
        'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
        'edited': comment.updated_at - comment.created_at > timedelta(seconds=1),
        'can_edit': is_author,
        'can_delete': is_author or (user.is_authenticated and user.is_staff),
    }


def json_login_required(view):
    """Like login_required, but answers AJAX calls with a 401 instead of a redirect."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Log in to comment.'}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def _form_error(form):
    return JsonResponse({'error': form.errors['body'][0]}, status=400)


# ---------- Map ----------
def home(request):
    communities = Community.objects.filter(is_active=True)
    categories = Category.objects.all()

    issues = (
        Issue.objects
        .select_related('category', 'community', 'reported_by', 'location')
        .prefetch_related('images', 'comments__author')
    )

    active_community = None
    community_id = request.GET.get('community')
    if community_id and community_id.isdigit():
        active_community = communities.filter(pk=community_id).first()
        if active_community:
            issues = issues.filter(community=active_community)

    only_mine = request.GET.get('mine') == '1' and request.user.is_authenticated
    if only_mine:
        issues = issues.filter(reported_by=request.user)

    q = request.GET.get('q', '').strip()
    if q:
        issues = issues.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(location__address__icontains=q)
        )

    user = request.user
    managed = managed_community_ids(user)

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
            'comments': [
                serialize_comment(c, user)
                for c in issue.comments.all()
            ],
            'detail_url': reverse('issue_detail', args=[issue.id]),
            'edit_url': reverse('issue_update', args=[issue.id]),
            'delete_url': reverse('issue_delete', args=[issue.id]),
            'can_edit': user.is_authenticated and (
                user.is_staff or issue.reported_by_id == user.id or issue.community_id in managed
            ),
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

@login_required
def profile_settings(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            if request.POST.get('remove_avatar') and not request.FILES.get('avatar'):
                profile.avatar.delete(save=False)
                profile.avatar = ''
                profile.save()
            else:
                profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile_settings')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'profile_settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        # base.html sidebar needs these
        'communities': Community.objects.filter(is_active=True),
    })


# ---------- Communities ----------
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


# ---------- Issues: Create ----------
@login_required
def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(user=request.user)
            messages.success(request, 'Your issue has been reported.')
            return redirect('issue_detail', pk=issue.pk)
    else:
        lat, lng = request.GET.get('lat'), request.GET.get('lng')
        if not (lat and lng):
            messages.info(request, 'Click a spot on the map to report an issue.')
            return redirect('home')
        form = IssueForm(initial={'latitude': lat, 'longitude': lng})

    return render(request, 'Issues/issue_form.html', {'form': form, 'issue': None})


# ---------- Issues: Read ----------
def _render_detail(request, issue, status_form=None):
    user = request.user
    manager = is_manager(user, issue)
    editable = is_owner(user, issue) or manager
    if editable and status_form is None:
        status_form = IssueStatusForm(issue=issue, manager=manager)
    return render(request, 'Issues/issue_detail.html', {
        'issue': issue,
        'images': issue.images.all(),
        'updates': issue.updates.select_related('updated_by'),
        'can_edit': editable,
        'is_manager': manager,
        'status_form': status_form,
    })


def issue_detail(request, pk):
    issue = get_object_or_404(
        Issue.objects.select_related('category', 'community', 'reported_by', 'location'),
        pk=pk,
    )
    return _render_detail(request, issue)


# ---------- Issues: Update ----------
@login_required
def issue_update(request, pk):
    issue = get_object_or_404(Issue.objects.select_related('location'), pk=pk)
    if not can_edit(request.user, issue):
        return HttpResponseForbidden('You can only edit your own issues.')

    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES, instance=issue)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'Issue updated.')
            return redirect('issue_detail', pk=issue.pk)
    else:
        form = IssueForm(instance=issue)

    return render(request, 'Issues/issue_form.html', {'form': form, 'issue': issue})


@login_required
@require_POST
def issue_status(request, pk):
    """Status change + history entry. Resolving requires a proof photo."""
    issue = get_object_or_404(
        Issue.objects.select_related('category', 'community', 'reported_by', 'location'),
        pk=pk,
    )
    if not can_edit(request.user, issue):
        return HttpResponseForbidden()

    manager = is_manager(request.user, issue)
    form = IssueStatusForm(request.POST, request.FILES, issue=issue, manager=manager)
    if not form.is_valid():
        return _render_detail(request, issue, status_form=form)

    with transaction.atomic():
        proof = form.cleaned_data.get('proof_image')
        if proof:
            IssueImage.objects.create(
                issue=issue, uploaded_by=request.user,
                image=proof, image_type='Resolution Proof',
            )
        previous = issue.status
        issue.status = form.cleaned_data['status']
        if manager and form.cleaned_data.get('priority'):
            issue.priority = form.cleaned_data['priority']
        issue.save()
        IssueUpdate.objects.create(
            issue=issue, updated_by=request.user,
            previous_status=previous, new_status=issue.status,
            remarks=form.cleaned_data.get('remarks', ''),
        )

    messages.success(request, f'Status set to {issue.status}.')
    return redirect('issue_detail', pk=issue.pk)


# ---------- Issues: Delete ----------
@login_required
def issue_delete(request, pk):
    issue = get_object_or_404(Issue.objects.select_related('location'), pk=pk)
    if not can_edit(request.user, issue):
        return HttpResponseForbidden('You can only delete your own issues.')

    if request.method == 'POST':
        # Issue.location is a OneToOne with CASCADE, so deleting the Location
        # removes the Issue (and its images/updates) and leaves no orphan row.
        issue.location.delete()
        messages.success(request, 'Issue deleted.')
        return redirect('home')

    return render(request, 'Issues/issue_confirm_delete.html', {'issue': issue})


# ---------- Comments (JSON endpoints) ----------
@require_POST
@json_login_required
def comment_create(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    form = IssueCommentForm(request.POST)
    if not form.is_valid():
        return _form_error(form)

    comment = IssueComment.objects.create(
        issue=issue,
        author=request.user,
        body=form.cleaned_data['body'],
    )
    return JsonResponse({'comment': serialize_comment(comment, request.user)}, status=201)


@require_POST
@json_login_required
def comment_update(request, pk):
    comment = get_object_or_404(IssueComment.objects.select_related('author'), pk=pk)
    if comment.author_id != request.user.id:
        return JsonResponse({'error': 'You can only edit your own comments.'}, status=403)

    form = IssueCommentForm(request.POST, instance=comment)
    if not form.is_valid():
        return _form_error(form)

    comment = form.save()
    return JsonResponse({'comment': serialize_comment(comment, request.user)})


@require_POST
@json_login_required
def comment_delete(request, pk):
    comment = get_object_or_404(IssueComment, pk=pk)
    if comment.author_id != request.user.id and not request.user.is_staff:
        return JsonResponse({'error': 'You can only delete your own comments.'}, status=403)

    comment.delete()
    return JsonResponse({'deleted': pk})
