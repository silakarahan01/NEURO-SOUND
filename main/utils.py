"""
Utility functions shared across views and business logic.
"""
from __future__ import annotations

import logging
import secrets
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional, Tuple

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .constants import VERIFICATION_CODE_EXPIRY_MINUTES
from .models import UserSubscription

if TYPE_CHECKING:
    from .models import Notification, User

logger = logging.getLogger('main')


def get_subscription_info(user: 'User') -> dict:
    """
    Get current subscription info for a user.

    Returns a dict with subscription details and active status.
    This function consolidates logic that was previously duplicated
    in patient.py and psychologist.py.

    Args:
        user: User instance

    Returns:
        dict with keys: 'subscription', 'is_active', 'days_remaining'
    """
    today = timezone.now().date()

    try:
        subscription = user.usersubscription_set.latest('created_at')
    except UserSubscription.DoesNotExist:
        return {
            'subscription': None,
            'is_active': False,
            'days_remaining': 0,
        }

    is_active = subscription.is_active and subscription.end_date >= today
    days_remaining = (subscription.end_date - today).days if is_active else 0

    return {
        'subscription': subscription,
        'is_active': is_active,
        'days_remaining': days_remaining,
    }


def calculate_subscription_end_date(days: int = 30) -> date:
    """Calculate subscription end date from today."""
    return timezone.now().date() + timedelta(days=days)


def is_valid_frequency(frequency_key: str) -> bool:
    """Validate if a frequency key is in the allowed list."""
    from .constants import FREQUENCIES
    return frequency_key in FREQUENCIES


def get_frequency_display(frequency_key: str) -> Optional[dict]:
    """Get human-readable frequency display info, or None if not found."""
    from .constants import FREQUENCIES
    return FREQUENCIES.get(frequency_key)


def generate_verification_code() -> str:
    """6 haneli sıfır-yastıklı kriptografik rastgele kod üretir."""
    return f"{secrets.randbelow(1000000):06d}"


def issue_verification_code(user: 'User') -> str:
    """Kullanıcıya yeni doğrulama kodu atar, süresini ayarlar ve e-posta gönderir.

    HTML + plain-text alternative içerikli e-posta render eder. send_mail
    başarısız olursa loglanır; çağıran kod akışı kesintiye uğramaz.
    """
    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_expires_at = (
        timezone.now() + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)
    )
    user.save(update_fields=['verification_code', 'verification_code_expires_at'])

    context = {
        'user': user,
        'first_name': user.first_name,
        'code': code,
        'expiry_minutes': VERIFICATION_CODE_EXPIRY_MINUTES,
    }
    subject = 'NEURO SOUND • E-posta Doğrulama Kodunuz'
    text_body = render_to_string('emails/verification_email.txt', context)
    html_body = render_to_string('emails/verification_email.html', context)

    # Geliştirme ortamında kodu her zaman terminale bas
    print(f"\n{'='*50}")
    print(f"  DOĞRULAMA KODU — {user.username} ({user.email})")
    print(f"  KOD: {code}  ({VERIFICATION_CODE_EXPIRY_MINUTES} dk geçerli)")
    print(f"{'='*50}\n", flush=True)

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        logger.info("Doğrulama kodu gönderildi: %s", user.username)
    except Exception as exc:
        logger.error("Doğrulama e-postası gönderilemedi (%s): %s", user.username, exc)
    return code


def verification_code_is_valid(
    user: 'User', entered_code: Optional[str],
) -> Tuple[bool, Optional[str]]:
    """Girilen kodu timing-safe şekilde doğrular ve süresini kontrol eder."""
    if not user.verification_code:
        return False, "Henüz size kod gönderilmemiş."
    if not secrets.compare_digest(user.verification_code, entered_code or ''):
        return False, "Hatalı doğrulama kodu."
    if user.verification_code_expires_at and timezone.now() > user.verification_code_expires_at:
        return False, "Doğrulama kodunun süresi dolmuş."
    return True, None


def create_notification(
    user: Optional['User'], message: str, link_url: str = '',
) -> Optional['Notification']:
    """Kullanıcıya bir bildirim kaydı oluşturur.

    Çağıran kodun akışını engellememesi için herhangi bir DB hatası
    yutulup loglanır (notifications kritik path değil).
    """
    from .models import Notification
    if not user or not message:
        return None
    try:
        return Notification.objects.create(
            user=user,
            message=message[:255],
            link_url=link_url or '',
        )
    except Exception as exc:
        logger.error("Notification oluşturulamadı (%s): %s", getattr(user, 'username', '?'), exc)
        return None
