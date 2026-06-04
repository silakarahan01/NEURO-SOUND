"""
Context processors — her template render'ında çalışan global context sağlayıcılar.
settings.TEMPLATES[0]['OPTIONS']['context_processors']'a eklenir.
"""


def notifications(request):
    """Authenticated kullanıcılar için okunmamış bildirim sayısı ve son 5 bildirim.

    Anonim kullanıcılar için boş değerler döner — template'de safe kullanım için.
    Sayı sorgusu hızlı (index'li) ve liste yalnızca açılır panel için 5 ile sınırlı.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'unread_notifications_count': 0, 'recent_notifications': []}

    qs = request.user.notifications.all()
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': list(qs[:5]),
    }
