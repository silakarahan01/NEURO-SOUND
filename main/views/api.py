import json
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

from ..models import ListeningLog, Notification, Prescription

logger = logging.getLogger('main')


@require_POST
@login_required
def save_progress(request):
    """
    Dinleme oturumu ilerlemesini kaydeder.
    Beklenen JSON: { completed: bool, duration: int (saniye), prescription_id: int|null }
    """
    try:
        data = json.loads(request.body)
        completed = data.get('completed', False)
        duration = int(data.get('duration', 0))
        pres_id = data.get('prescription_id')

        target_prescription = None
        if pres_id:
            target_prescription = Prescription.objects.filter(
                id=pres_id, patient=request.user
            ).first()
        if not target_prescription:
            target_prescription = Prescription.objects.filter(
                patient=request.user
            ).order_by('-created_at').first()

        if target_prescription:
            frequency = target_prescription.frequency
        else:
            # Bireysel kullanıcı: frontend'den gelen frekans değerini kullan
            frequency = data.get('frequency') or None

        log, _ = ListeningLog.objects.get_or_create(
            user=request.user,
            date=timezone.now().date(),
            frequency=frequency,
        )
        log.duration_listened = duration
        if completed:
            log.is_completed = True

        log.save()
        logger.info(f"İlerleme kaydedildi: {request.user.username} — {duration}s (tamamlandı: {completed})")
        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Geçersiz JSON verisi.'}, status=400)
    except (ValueError, TypeError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
def mark_notification_read(request, notification_id):
    """Tek bildirimi okundu olarak işaretler. AJAX'tan çağrılır."""
    updated = Notification.objects.filter(
        id=notification_id, user=request.user, is_read=False,
    ).update(is_read=True)
    return JsonResponse({'status': 'success', 'updated': updated})


@require_POST
@login_required
def mark_all_notifications_read(request):
    """Kullanıcının okunmamış tüm bildirimlerini okundu yapar."""
    updated = Notification.objects.filter(
        user=request.user, is_read=False,
    ).update(is_read=True)
    return JsonResponse({'status': 'success', 'updated': updated})
