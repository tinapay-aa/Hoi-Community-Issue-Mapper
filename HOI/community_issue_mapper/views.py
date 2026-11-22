from django.db.models import Q
from django.shortcuts import render

from .models import Category, Community, Issue


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


