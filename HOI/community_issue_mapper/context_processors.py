from .models import Community


def sidebar(request):
    return {'communities': Community.objects.filter(is_active=True)}