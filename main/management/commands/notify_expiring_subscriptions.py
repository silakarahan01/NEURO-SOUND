"""
Aboneliği bitmek üzere olan kullanıcılara bildirim gönderir.

Çalıştırma:
    python manage.py notify_expiring_subscriptions

Cron örneği (her gün 09:00):
    0 9 * * * /path/to/venv/bin/python /path/to/manage.py notify_expiring_subscriptions
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import Notification, UserSubscription
from main.utils import create_notification

logger = logging.getLogger('main')

THRESHOLDS = [7, 3, 1]  # kaç gün kala bildirim gönderilsin


class Command(BaseCommand):
    help = "Aboneliği bitmek üzere olan kullanıcılara bildirim gönderir."

    def handle(self, *args, **options):
        today = timezone.now().date()
        total_sent = 0

        for days_left in THRESHOLDS:
            target_date = today + timedelta(days=days_left)

            expiring = UserSubscription.objects.filter(
                is_active=True,
                end_date=target_date,
            ).select_related('user', 'plan')

            for sub in expiring:
                user = sub.user
                if not user.is_active:
                    continue

                # Bugün aynı eşik için zaten bildirim gönderildiyse atla
                already_sent = Notification.objects.filter(
                    user=user,
                    message__contains=f"{days_left} gün",
                    created_at__date=today,
                ).exists()

                if already_sent:
                    continue

                if days_left == 1:
                    msg = "⚠️ Aboneliğiniz yarın sona eriyor! Kesintisiz devam etmek için yenileyin."
                else:
                    msg = f"⏳ Aboneliğinizin bitmesine {days_left} gün kaldı. Yenilemeyi unutmayın."

                create_notification(user, msg, link_url='/payment/')
                total_sent += 1
                self.stdout.write(
                    f"  Bildirim → {user.username} ({days_left} gün kaldı, bitiş: {sub.end_date})"
                )

        self.stdout.write(self.style.SUCCESS(
            f"Tamamlandı. {total_sent} bildirim gönderildi."
        ))
        logger.info("notify_expiring_subscriptions: %d bildirim gönderildi", total_sent)
