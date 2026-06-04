from django.shortcuts import redirect
from django.utils import timezone
from .models import UserSubscription

# Bu URL'lere abonelik olmadan erişilebilir (startswith kontrolü yapılır)
EXEMPT_PREFIXES = [
    '/login/',
    '/register/',
    '/logout/',
    '/subscription/payment/',
    '/password-reset/',
    '/reset/',
    '/ns-yonetim/',
    '/admin/',
    '/contact/',
    '/kvkk/',
    '/terms/',
    '/privacy/',
    '/cookie-policy/',
    '/frequencies/',
    '/static/',
    '/media/',
]

# Tam eşleşme gerektiren path'ler (startswith ile '/' her şeyi muaf ederdi)
EXEMPT_EXACT = {'/', ''}

_SESSION_KEY = '_sub_active'


def _has_active_subscription(request):
    """Abonelik durumunu session cache'den okur; yoksa DB'den sorgulayıp kaydeder."""
    cached = request.session.get(_SESSION_KEY)
    if cached is not None:
        return cached
    today = timezone.now().date()
    active = UserSubscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gte=today,
    ).exists()
    request.session[_SESSION_KEY] = active
    return active


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            path = request.path_info

            is_exempt = (
                path in EXEMPT_EXACT
                or any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES)
            )

            if not is_exempt:
                if not _has_active_subscription(request):
                    request.session[_SESSION_KEY] = False
                    return redirect('payment_view')

        return self.get_response(request)
