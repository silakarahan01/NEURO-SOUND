import logging
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from ..models import (
    Prescription, ListeningLog, SubscriptionPlan,
    UserSubscription, MusicTrack, SurveyResponse,
)
from ..utils import get_subscription_info, create_notification
from ..constants import FREQUENCIES, SUBSCRIPTION_PRICES
from ..forms import SurveyForm, SURVEY_QUESTIONS
from ..ml import recommender

logger = logging.getLogger('main')


# Build frequency data from constants for backward compatibility
def _build_frequencies():
    """Convert frequency constants to legacy format."""
    frequencies = []
    freq_keys = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    icons = ['fa-moon', 'fa-wind', 'fa-spa', 'fa-bolt', 'fa-fire']
    colors = ['violet', 'blue', 'cyan', 'green', 'amber']

    for key, icon, color in zip(freq_keys, icons, colors):
        freq_data = FREQUENCIES.get(key)
        if freq_data:
            frequencies.append({
                'value': key.capitalize(),
                'label': freq_data['name'],
                'desc': f"{freq_data['frequency']} ({freq_data['description']})",
                'icon': icon,
                'color_cls': color,
            })
    return frequencies


STANDARD_FREQUENCIES = _build_frequencies()


@login_required
def patient_dashboard(request):
    """Danışan paneli: frekans seçimi, dinleme takibi, geçmiş."""
    if request.user.is_psychologist:
        return redirect('psychologist_dashboard')
    if request.user.is_superuser:
        return redirect('super_admin_dashboard')

    is_individual = getattr(request.user, 'is_individual', False)
    has_assigned_psychologist = bool(request.user.assigned_psychologist_id)
    free_individual_mode = is_individual and not has_assigned_psychologist
    standard_frequencies = []

    if free_individual_mode:
        standard_frequencies = STANDARD_FREQUENCIES
        selected_freq_val = request.GET.get('freq', 'Delta')
        selected_freq_info = next(
            (f for f in standard_frequencies if f['value'] == selected_freq_val),
            standard_frequencies[0]
        )
        try:
            custom_duration = int(request.GET.get('duration', 30))
        except ValueError:
            custom_duration = 30

        prescription = Prescription(
            patient=request.user,
            frequency=selected_freq_info['value'],
            duration_minutes=custom_duration,
            total_days=1,
            notes="Bireysel Serbest Çalışma Modu",
            created_at=timezone.now()
        )
        all_prescriptions = []
    else:
        all_prescriptions = Prescription.objects.filter(patient=request.user).order_by('-created_at')
        selected_pres_id = request.GET.get('pres_id')
        prescription = None
        if selected_pres_id:
            prescription = all_prescriptions.filter(id=selected_pres_id).first()
        if not prescription:
            prescription = all_prescriptions.first()

    today = timezone.now().date()

    # Only create ListeningLog if user has an active prescription or is in free mode
    today_log = None
    if prescription:
        today_log, _ = ListeningLog.objects.get_or_create(
            user=request.user,
            date=today,
            frequency=prescription.frequency,
        )

    timer_start_seconds = (prescription.duration_minutes if prescription else 15) * 60
    today_listened_seconds = today_log.duration_listened if today_log else 0

    thirty_days_ago = today - timedelta(days=30)
    history = ListeningLog.objects.filter(
        user=request.user, date__gte=thirty_days_ago
    ).order_by('-date')

    selected_music = request.GET.get('bg_music', None)
    music_title = request.GET.get('title', 'Sessiz Mod')
    music_tracks = MusicTrack.objects.filter(is_active=True).order_by('order', 'title')

    sub_info = get_subscription_info(request.user)
    subscription = sub_info['subscription']
    days_left = sub_info['days_remaining']

    # ── Anket / ML öneri durumu (sadece bireysel kullanıcılar) ──
    latest_survey = None
    show_survey_prompt = False
    plan_expired = False

    if is_individual:
        latest_survey = SurveyResponse.objects.filter(user=request.user).first()
        if latest_survey is None:
            show_survey_prompt = True
        elif latest_survey.is_expired:
            plan_expired = True
            show_survey_prompt = True
            if not latest_survey.renewal_notified:
                create_notification(
                    request.user,
                    '15 günlük planınız tamamlandı! Yeni anket ile programınızı güncelleyin.',
                    '/patient/survey/',
                )
                latest_survey.renewal_notified = True
                latest_survey.save(update_fields=['renewal_notified'])

    return render(request, 'dashboard/patient_dashboard.html', {
        'all_prescriptions': all_prescriptions,
        'standard_frequencies': standard_frequencies,
        'prescription': prescription,
        'selected_music': selected_music,
        'music_title': music_title,
        'music_tracks': music_tracks,
        'today_log': today_log,
        'history': history,
        'timer_start_seconds': timer_start_seconds,
        'today_listened_seconds': today_listened_seconds,
        'subscription': subscription,
        'days_left': days_left,
        'latest_survey': latest_survey,
        'show_survey_prompt': show_survey_prompt,
        'plan_expired': plan_expired,
    })


@login_required
def survey_view(request):
    """Bireysel kullanıcı anket formu — ML frekans önerisi oluşturur."""
    if not getattr(request.user, 'is_individual', False):
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                result = recommender.recommend(**data)
            except Exception:
                logger.exception("ML modeli çalışırken hata oluştu.")
                messages.error(request, 'Öneri sistemi şu anda kullanılamıyor. Lütfen tekrar deneyin.')
                return render(request, 'dashboard/survey_form.html', {
                    'form': form,
                    'survey_questions': SURVEY_QUESTIONS,
                })

            today = timezone.now().date()
            plan_days = result.get('days', 15)
            SurveyResponse.objects.create(
                user=request.user,
                sleep_quality=data['sleep_quality'],
                stress_level=data['stress_level'],
                focus_level=data['focus_level'],
                mood_score=data['mood_score'],
                anxiety_level=data['anxiety_level'],
                fatigue_level=data['fatigue_level'],
                recommended_frequency=result['frequency'],
                recommended_minutes=result['minutes'],
                recommended_days=plan_days,
                ml_confidence=result['confidence'],
                plan_start_date=today,
                plan_expires_at=today + timedelta(days=plan_days),
            )
            messages.success(
                request,
                f'{plan_days} günlük programınız oluşturuldu! İyi dinlemeler.',
            )
            return redirect('patient_dashboard')
    else:
        form = SurveyForm(initial={f: 5 for f in SurveyForm.base_fields})

    survey_fields = [
        {'field': form[fname], 'label': label, 'hint': hint}
        for fname, label, hint in SURVEY_QUESTIONS
    ]
    return render(request, 'dashboard/survey_form.html', {
        'form': form,
        'survey_fields': survey_fields,
    })


@login_required
def music_library(request):
    """Müzik kütüphanesi: aktif parçaları listeler."""
    tracks = MusicTrack.objects.filter(is_active=True).order_by('order', 'title')
    back_params = {}
    if request.GET.get('pres_id'):
        back_params['pres_id'] = request.GET['pres_id']
    if request.GET.get('freq'):
        back_params['freq'] = request.GET['freq']
    if request.GET.get('duration'):
        back_params['duration'] = request.GET['duration']
    back_qs = '&'.join(f'{k}={v}' for k, v in back_params.items())
    return render(request, 'pages/music_library.html', {'tracks': tracks, 'back_qs': back_qs})


@login_required
@transaction.atomic
def payment_view(request):
    """Abonelik satın alma / yenileme (simülasyon)."""
    selected_plan_type = 'PSYCHOLOGIST' if request.user.is_psychologist else 'INDIVIDUAL'
    plan_price = SUBSCRIPTION_PRICES.get(selected_plan_type, 50.00)

    plan, _ = SubscriptionPlan.objects.update_or_create(
        name=selected_plan_type,
        defaults={'price': plan_price}
    )

    if request.method == 'POST':
        length_days = 30
        sub, created = UserSubscription.objects.get_or_create(
            user=request.user,
            plan=plan,
            defaults={
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=length_days),
                'is_active': True,
            }
        )
        if not created:
            sub.start_date = timezone.now().date()
            sub.end_date = timezone.now().date() + timedelta(days=length_days)
            sub.is_active = True
            sub.save()

        # Delete other subscriptions (keep only the current one)
        UserSubscription.objects.filter(user=request.user).exclude(id=sub.id).delete()
        request.session['_sub_active'] = True  # middleware session cache'ini güncelle
        logger.info(f"Abonelik yenilendi: {request.user.username}")
        messages.success(request, 'Ödeme başarılı! Aboneliğiniz 30 gün uzatıldı.')

        if request.user.is_psychologist:
            return redirect('psychologist_dashboard')
        return redirect('patient_dashboard')

    today = timezone.now().date()
    has_active_sub = UserSubscription.objects.filter(
        user=request.user, is_active=True, end_date__gte=today
    ).exists()

    return render(request, 'dashboard/payment.html', {
        'plan': plan,
        'card_holder_name': request.user.get_full_name() or request.user.username,
        'is_renewal': has_active_sub,
    })
