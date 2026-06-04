import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum

from ..forms import PrescriptionForm, SessionNoteForm
from ..models import User, Prescription, ListeningLog, SessionNote
from ..utils import get_subscription_info, create_notification

logger = logging.getLogger('main')


@login_required
def psychologist_dashboard(request):
    """Psikolog paneli: hasta listesi ve reçete yönetimi.

    POST: Multi-frequency AJAX kullanılır. Frontend her frekans için ayrı
    POST atar; her istek tek bir reçete oluşturur ve JSON döner.
    """
    if not request.user.is_psychologist:
        if request.user.is_superuser:
            return redirect('super_admin_dashboard')
        return redirect('patient_dashboard')

    patients = User.objects.filter(assigned_psychologist=request.user)
    prescriptions = Prescription.objects.filter(assigned_by=request.user).order_by('-created_at')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        post_data = {
            'patient': request.POST.get('patient_id'),
            'frequency': request.POST.get('frequency'),
            'duration_minutes': request.POST.get('duration'),
            'total_days': request.POST.get('days'),
            'notes': request.POST.get('notes', ''),
        }
        form = PrescriptionForm(post_data, psychologist=request.user)

        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.assigned_by = request.user

            force = request.POST.get('force') == 'true'
            if not force and is_ajax:
                already_done = ListeningLog.objects.filter(
                    user=prescription.patient,
                    frequency=prescription.frequency,
                    date=timezone.now().date(),
                    is_completed=True,
                ).exists()
                if already_done:
                    return JsonResponse({
                        'success': False,
                        'warning': True,
                        'message': (
                            f'Bu danışan bugün {prescription.get_frequency_display()} frekansını '
                            f'zaten tamamladı. Yine de eklemek istiyor musunuz?'
                        ),
                    })

            prescription.save()
            logger.info(
                "Reçete oluşturuldu: %s → %s (%s)",
                request.user.username, prescription.patient.username, prescription.frequency,
            )
            create_notification(
                prescription.patient,
                f"Yeni reçete: {prescription.get_frequency_display()} "
                f"({prescription.duration_minutes} dk × {prescription.total_days} gün)",
                link_url='/patient/',
            )
            if is_ajax:
                return JsonResponse({'success': True, 'prescription_id': prescription.id})
            messages.success(request, "Reçete başarıyla oluşturuldu.")
            return redirect('psychologist_dashboard')

        if is_ajax:
            readable = {
                field: list(errs)
                for field, errs in form.errors.items()
                if field != '__all__'
            }
            if form.non_field_errors():
                readable['genel'] = list(form.non_field_errors())
            return JsonResponse({'success': False, 'errors': readable}, status=400)
        for field_errors in form.errors.values():
            for err in field_errors:
                messages.error(request, err)
        return redirect('psychologist_dashboard')

    for pres in prescriptions:
        completed_days = ListeningLog.objects.filter(
            user=pres.patient,
            frequency=pres.frequency,
            is_completed=True,
            date__gt=pres.created_at.date(),
        ).count()
        pres.is_patient_completed = completed_days >= pres.total_days

    sub_info = get_subscription_info(request.user)
    subscription = sub_info['subscription']
    days_left = sub_info['days_remaining']

    return render(request, 'dashboard/psychologist_dashboard.html', {
        'patients': patients,
        'prescriptions': prescriptions,
        'subscription': subscription,
        'days_left': days_left,
    })


@login_required
def prescription_update_view(request, pres_id):
    """Psikolog mevcut reçeteyi düzenler."""
    if not request.user.is_psychologist:
        return redirect('landing')

    prescription = get_object_or_404(Prescription, id=pres_id, assigned_by=request.user)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription, psychologist=request.user)
        if form.is_valid():
            form.save()
            logger.info("Reçete güncellendi: %s id=%s", request.user.username, prescription.id)
            messages.success(request, "Reçete güncellendi.")
            return redirect('psychologist_dashboard')
    else:
        form = PrescriptionForm(instance=prescription, psychologist=request.user)

    return render(request, 'dashboard/prescription_form.html', {
        'form': form,
        'prescription': prescription,
        'mode': 'edit',
    })


@require_POST
@login_required
def delete_prescription(request, pres_id):
    """Psikolog kendi reçetesini silebilir."""
    if not request.user.is_psychologist:
        return redirect('landing')

    prescription = get_object_or_404(Prescription, id=pres_id, assigned_by=request.user)
    patient_name = prescription.patient.first_name
    prescription.delete()
    messages.warning(request, f"{patient_name} adlı danışanın reçetesi silindi.")
    return redirect('psychologist_dashboard')


@login_required
def patient_detail_view(request, patient_id):
    """Psikoloğun hastasının detaylarını, notlarını ve dinleme geçmişini gördüğü sayfa."""
    if not request.user.is_psychologist:
        return redirect('landing')

    patient = get_object_or_404(User, id=patient_id, assigned_psychologist=request.user)

    note_form = SessionNoteForm()

    if request.method == 'POST':
        general_notes = request.POST.get('psychologist_notes')
        if general_notes is not None:
            patient.psychologist_notes = general_notes
            patient.save(update_fields=['psychologist_notes'])

        # Seans notu sadece note alanı doldurulduysa kaydedilir
        if request.POST.get('note'):
            note_form = SessionNoteForm(request.POST)
            if note_form.is_valid():
                session_note = note_form.save(commit=False)
                session_note.patient = patient
                session_note.created_by = request.user
                session_note.save()
                messages.success(request, "Yeni seans notu eklendi.")
                return redirect('patient_detail', patient_id=patient.id)
            messages.error(request, "Seans notu kaydedilemedi. Lütfen alanları kontrol edin.")
        else:
            return redirect('patient_detail', patient_id=patient.id)

    active_prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    session_notes = SessionNote.objects.filter(patient=patient).order_by('-date', '-created_at')
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    logs = ListeningLog.objects.filter(user=patient, date__gte=thirty_days_ago).order_by('-date')

    total_listened_seconds = logs.aggregate(Sum('duration_listened'))['duration_listened__sum'] or 0
    total_days_logged = logs.values('date').distinct().count()

    return render(request, 'dashboard/patient_detail.html', {
        'patient': patient,
        'prescriptions': active_prescriptions,
        'logs': logs,
        'session_notes': session_notes,
        'note_form': note_form,
        'total_minutes': round(total_listened_seconds / 60, 1),
        'total_days_logged': total_days_logged,
    })


@login_required
@require_POST
def delete_session_note_view(request, note_id):
    note = get_object_or_404(SessionNote, id=note_id, created_by=request.user)
    patient_id = note.patient_id
    note.delete()
    return redirect('patient_detail', patient_id=patient_id)
