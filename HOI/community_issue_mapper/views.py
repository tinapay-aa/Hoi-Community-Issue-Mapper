from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, UserForm
from .models import Category, Community, Issue, Profile


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


