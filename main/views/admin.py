import os
import secrets
import logging
import functools
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, Prefetch
from django_ratelimit.decorators import ratelimit

from ..models import (
    User, Prescription, ListeningLog, ContactMessage, MusicTrack, SurveyResponse,
)
from ..constants import VERIFICATION_CODE_EXPIRY_MINUTES
from ..utils import issue_verification_code

logger = logging.getLogger('main')

# ─── Dosya Yükleme Güvenliği ─────────────────────────────────────
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
MAX_AUDIO_SIZE_BYTES = 1024 * 1024 * 1024  # 1 GB


def _validate_audio_file(uploaded_file):
    """Ses dosyasının uzantısını ve boyutunu doğrular. Hata varsa ValueError fırlatır."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise ValueError(f"Geçersiz dosya uzantısı. İzin verilenler: {allowed}")
    if uploaded_file.size > MAX_AUDIO_SIZE_BYTES:
        raise ValueError("Dosya boyutu 1GB sınırını aşıyor.")


# ─── Süper Admin Kontrol Dekoratörü ──────────────────────────────

def superuser_required(view_func):
    """Süper yönetici olmayan kullanıcıları landing'e yönlendirir."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


# ─── Dashboard ───────────────────────────────────────────────────

@superuser_required
def super_admin_dashboard(request):
    """Ana Yönetim Paneli: Genel istatistikler."""
    total_patients = User.objects.filter(is_superuser=False, is_psychologist=False).count()
    total_psychologists = User.objects.filter(is_psychologist=True, is_active=True).count()
    total_individual = User.objects.filter(is_individual=True).count()
    pending_count = User.objects.filter(is_psychologist=True, is_active=False).count()
    unread_count = ContactMessage.objects.filter(is_read=False).count()

    total_seconds = ListeningLog.objects.aggregate(total=Sum('duration_listened'))['total'] or 0
    total_hours = round(total_seconds / 3600, 1)

    top_frequencies_raw = (
        ListeningLog.objects
        .exclude(frequency__isnull=True).exclude(frequency='')
        .values('frequency')
        .annotate(session_count=Count('id'), total_seconds=Sum('duration_listened'))
        .order_by('-session_count')[:5]
    )
    top_frequencies = [
        {
            'frequency': f['frequency'],
            'session_count': f['session_count'],
            'total_minutes': round((f['total_seconds'] or 0) / 60, 1),
        }
        for f in top_frequencies_raw
    ]
    music_tracks = MusicTrack.objects.filter(is_active=True).order_by('order', 'title')[:8]

    # Anket istatistikleri
    total_surveys = SurveyResponse.objects.count()
    survey_freq_dist = (
        SurveyResponse.objects
        .values('recommended_frequency')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return render(request, 'dashboard/super_admin.html', {
        'total_patients': total_patients,
        'total_psychologists': total_psychologists,
        'total_individual': total_individual,
        'pending_count': pending_count,
        'unread_count': unread_count,
        'total_hours': total_hours,
        'top_frequencies': top_frequencies,
        'music_tracks': music_tracks,
        'total_surveys': total_surveys,
        'survey_freq_dist': survey_freq_dist,
    })


@superuser_required
def admin_onaylar_view(request):
    """Onay bekleyen psikolog başvuruları."""
    pending_psychologists = User.objects.filter(is_psychologist=True, is_active=False)
    return render(request, 'dashboard/admin_onaylar.html', {'psychologists': pending_psychologists})


@superuser_required
def admin_formlar_view(request):
    """İletişim formu mesajları."""
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    unread_count = contact_messages.filter(is_read=False).count()
    return render(request, 'dashboard/admin_formlar.html', {
        'contact_messages': contact_messages,
        'unread_count': unread_count,
    })


@superuser_required
def admin_patients_view(request):
    """Danışan yönetimi: listeleme ve psikolog atama."""
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        psychologist_id = request.POST.get('psychologist_id')
        try:
            patient = User.objects.get(id=patient_id)
            if psychologist_id:
                # Validate that psychologist_id is actually a psychologist
                psy = User.objects.get(id=psychologist_id, is_psychologist=True)
                patient.assigned_psychologist = psy
                messages.success(request, f"{patient.username} adlı danışan {psy.username} isimli psikoloğa atandı.")
            else:
                patient.assigned_psychologist = None
                messages.info(request, f"{patient.username} için atama kaldırıldı.")
            patient.save()
        except User.DoesNotExist:
            messages.error(request, "İşlem sırasında bir hata oluştu.")
        return redirect('admin_patients')

    patients = User.objects.filter(
        is_psychologist=False, is_superuser=False
    ).prefetch_related(
        Prefetch('listeninglog_set', queryset=ListeningLog.objects.order_by('-date'), to_attr='all_logs')
    )
    psychologists = User.objects.filter(is_psychologist=True, is_active=True)

    patient_stats = []
    for p in patients:
        logs = p.all_logs
        total_seconds = sum(log.duration_listened for log in logs)
        total_days = len({log.date for log in logs})
        history = [log.date for log in logs[:5]]
        patient_stats.append({
            'user': p,
            'total_minutes': round(total_seconds / 60, 1),
            'total_days': total_days,
            'history': history,
        })

    return render(request, 'dashboard/admin_patients.html', {
        'patient_stats': patient_stats,
        'psychologists': psychologists,
    })


@superuser_required
def admin_psychologists_view(request):
    """Psikolog performans takibi."""
    psychologists = User.objects.filter(
        is_psychologist=True, is_active=True
    ).prefetch_related(
        Prefetch(
            'assigned_patients',
            queryset=User.objects.prefetch_related(
                Prefetch('prescriptions', queryset=Prescription.objects.order_by('-created_at'), to_attr='all_prescriptions')
            ),
            to_attr='my_patients'
        )
    )

    psy_data = []
    for psy in psychologists:
        patient_list = []
        for pat in psy.my_patients:
            last_pres = pat.all_prescriptions[0] if pat.all_prescriptions else None
            patient_list.append({
                'name': f"{pat.first_name} {pat.last_name}",
                'username': pat.username,
                'last_prescription': last_pres,
            })
        psy_data.append({'user': psy, 'patients': patient_list})

    return render(request, 'dashboard/admin_psychologists.html', {'psy_data': psy_data})


@superuser_required
def admin_patient_detail_view(request, patient_id):
    """Süper Admin: danışanın tüm geçmişini görür (salt okunur)."""
    from ..models import SessionNote
    patient = get_object_or_404(User, id=patient_id, is_psychologist=False, is_superuser=False)
    prescriptions = Prescription.objects.filter(patient=patient).select_related('assigned_by').order_by('-created_at')
    session_notes = SessionNote.objects.filter(patient=patient).select_related('created_by').order_by('-date', '-created_at')
    logs = ListeningLog.objects.filter(user=patient).order_by('-date')

    total_seconds = logs.aggregate(total=Sum('duration_listened'))['total'] or 0
    total_days_logged = logs.values('date').distinct().count()
    completed_count = logs.filter(is_completed=True).count()

    return render(request, 'dashboard/admin_patient_detail.html', {
        'patient': patient,
        'prescriptions': prescriptions,
        'session_notes': session_notes,
        'logs': logs,
        'total_minutes': round(total_seconds / 60, 1),
        'total_days_logged': total_days_logged,
        'completed_count': completed_count,
    })


# ─── AJAX / Aksiyon View'ları ────────────────────────────────────

@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@login_required
def send_verification_code(request, user_id):
    """Psikolog onayı için 6 haneli kod üretir, süresi belirler ve gönderir."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Yetkisiz işlem'}, status=403)

    try:
        user = User.objects.get(id=user_id, is_psychologist=True, is_active=False)
        issue_verification_code(user)
        logger.info(f"Doğrulama kodu oluşturuldu: {user.username}")
        return JsonResponse({'status': 'success', 'message': 'Onay kodu oluşturuldu.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'})
    except Exception as e:
        logger.error(f"Doğrulama kodu hatası: {e}")
        return JsonResponse({'status': 'error', 'message': 'Sunucu hatası.'})


@require_POST
@login_required
def approve_psychologist(request):
    """Kodu doğrular ve psikoloğu aktifleştirir."""
    if not request.user.is_superuser:
        return redirect('landing')

    user_id = request.POST.get('user_id')
    code_entered = request.POST.get('code')

    try:
        user = User.objects.get(id=user_id, is_psychologist=True, is_active=False)

        # Timing-safe code comparison
        if not secrets.compare_digest(user.verification_code or '', code_entered or ''):
            messages.error(request, "Hatalı onay kodu!")
            return redirect('admin_onaylar')

        # Check if code has expired
        if user.verification_code_expires_at and timezone.now() > user.verification_code_expires_at:
            messages.error(request, "Onay kodu süresi dolmuş. Lütfen yeni bir kod isteyin.")
            return redirect('admin_onaylar')

        # Approve psychologist
        user.is_active = True
        user.verification_code = None
        user.verification_code_expires_at = None
        user.save()
        logger.info(f"Psikolog onaylandı: {user.username}")
        messages.success(request, f"{user.first_name} {user.last_name} hesabı onaylandı.")
    except User.DoesNotExist:
        messages.error(request, "Kullanıcı bulunamadı.")

    return redirect('admin_onaylar')


@require_POST
@login_required
def delete_user(request, user_id):
    """Kullanıcı silme (süper yönetici için)."""
    if not request.user.is_superuser:
        return redirect('landing')

    user = get_object_or_404(User, id=user_id)
    if user.id == request.user.id:
        messages.error(request, "Yönetici hesabınızı buradan silemezsiniz.")
        return redirect('super_admin_dashboard')

    is_psy = user.is_psychologist
    is_active = user.is_active
    name = f"{user.first_name} {user.last_name}"
    user.delete()
    logger.warning(f"Kullanıcı silindi: {name} (superuser: {request.user.username})")
    messages.success(request, f"{name} adlı kullanıcı ve tüm verileri başarıyla silindi.")

    if is_psy:
        return redirect('admin_onaylar') if not is_active else redirect('admin_psychologists')
    return redirect('admin_patients')


@require_POST
@login_required
def mark_message_read(request, msg_id):
    """İletişim mesajını okundu olarak işaretler (AJAX)."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error'}, status=403)
    ContactMessage.objects.filter(id=msg_id).update(is_read=True)
    return JsonResponse({'status': 'success'})


@superuser_required
def admin_muzik_view(request):
    """Müzik kütüphanesi yönetimi: ekleme, düzenleme, silme."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            icon = request.POST.get('icon', 'fa-music').strip()
            color = request.POST.get('color', 'violet').strip()
            audio_file = request.FILES.get('audio_file')

            # Validate and parse order
            try:
                order = int(request.POST.get('order') or 0)
            except (ValueError, TypeError):
                messages.error(request, "Sıra numarası geçerli bir tam sayı olmalıdır.")
                return redirect('admin_muzik')

            if not title or not audio_file:
                messages.error(request, "Başlık ve ses dosyası zorunludur.")
            else:
                try:
                    _validate_audio_file(audio_file)
                    MusicTrack.objects.create(
                        title=title, description=description,
                        icon=icon, color=color,
                        audio_file=audio_file, order=order
                    )
                    messages.success(request, f"'{title}' başarıyla eklendi.")
                except ValueError as e:
                    messages.error(request, str(e))

        elif action == 'edit':
            track = get_object_or_404(MusicTrack, id=request.POST.get('track_id'))
            track.title = request.POST.get('title', track.title).strip()
            track.description = request.POST.get('description', track.description).strip()
            track.icon = request.POST.get('icon', track.icon).strip()
            track.color = request.POST.get('color', track.color).strip()

            # Validate and parse order
            try:
                track.order = int(request.POST.get('order') or track.order)
            except (ValueError, TypeError):
                messages.error(request, "Sıra numarası geçerli bir tam sayı olmalıdır.")
                return redirect('admin_muzik')

            if request.FILES.get('audio_file'):
                try:
                    _validate_audio_file(request.FILES['audio_file'])
                    track.audio_file.delete(save=False)
                    track.audio_file = request.FILES['audio_file']
                except ValueError as e:
                    messages.error(request, str(e))
                    return redirect('admin_muzik')
            track.save()
            messages.success(request, f"'{track.title}' güncellendi.")

        elif action == 'delete':
            track = get_object_or_404(MusicTrack, id=request.POST.get('track_id'))
            name = track.title
            track.audio_file.delete(save=False)
            track.delete()
            messages.success(request, f"'{name}' silindi.")

        elif action == 'toggle':
            track = get_object_or_404(MusicTrack, id=request.POST.get('track_id'))
            track.is_active = not track.is_active
            track.save()

        return redirect('admin_muzik')

    tracks = MusicTrack.objects.all().order_by('order', 'title')
    return render(request, 'dashboard/admin_muzik.html', {
        'tracks': tracks,
        'icon_choices': MusicTrack.ICON_CHOICES,
        'color_choices': MusicTrack.COLOR_CHOICES,
    })
