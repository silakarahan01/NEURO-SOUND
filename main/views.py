from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, UserRegistrationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .models import User, Prescription, ListeningLog
from django.db.models import Sum, Count
import json
from django.core.mail import send_mail
from django.conf import settings
import random

# --- GİRİŞ VE TANITIM İŞLEMLERİ ---

def landing_view(request):
    """
    Tüm kullanıcılar için tanıtım (landing) sayfasını gösterir.
    Giriş yapmış kullanıcılar artık otomatik panellerine yönlendirilmez.
    (Navbar'daki Anasayfa linkinin çalışması için değiştirildi.)
    """
    return render(request, 'pages/landing.html')

def login_view(request):
    """
    Giriş işlemi. Custom form (UserLoginForm) kullanılır.
    """
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('super_admin_dashboard')
        if request.user.is_psychologist:
            return redirect('psychologist_dashboard')
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if user.is_superuser:
                return redirect('super_admin_dashboard')
            elif user.is_psychologist:
                return redirect('psychologist_dashboard')
            else:
                return redirect('patient_dashboard')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    """
    Kayıt işlemi. 
    """
    if request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Rol Kontrolü ve Yönlendirme
            if user.is_psychologist:
                # Psikolog hesabı pasif olarak (is_active=False) oluşturulur.
                messages.success(request, "Kaydınız başarıyla alındı! Psikolog hesabınız diploma kontrolü ve yönetici onayından sonra aktifleşecektir.")
                return redirect('login')
            else:
                messages.success(request, "Hesabınız başarıyla oluşturuldu! Lütfen giriş yapınız.")
                return redirect('login')
        else:
            # Form hatasını template'e ilet (İlk hatayı göster)
            error_message = None
            if form.errors:
                error_message = list(form.errors.values())[0][0]
            
            return render(request, 'accounts/register.html', {'form': form, 'error': error_message})
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


# --- SÜPER YÖNETİCİ (SUPER ADMIN) İŞLEMLERİ ---

@login_required
def super_admin_dashboard(request):
    """Ana Yönetim Paneli: Onay bekleyen psikologları listeler"""
    if not request.user.is_superuser:
        return redirect('landing')
    
    pending_psychologists = User.objects.filter(is_psychologist=True, is_active=False)
    return render(request, 'dashboard/super_admin.html', {'psychologists': pending_psychologists})

@login_required
def admin_patients_view(request):
    """Danışan Yönetimi: Listeleme, İstatistikler ve Psikolog Atama"""
    if not request.user.is_superuser:
        return redirect('landing')
    
    # Psikolog Atama İşlemi
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        psychologist_id = request.POST.get('psychologist_id')
        try:
            patient = User.objects.get(id=patient_id)
            if psychologist_id:
                psy = User.objects.get(id=psychologist_id)
                patient.assigned_psychologist = psy
                messages.success(request, f"{patient.username} adlı danışan {psy.username} isimli psikoloğa atandı.")
            else:
                patient.assigned_psychologist = None # Atamayı kaldır
                messages.info(request, f"{patient.username} için atama kaldırıldı.")
            patient.save()
        except User.DoesNotExist:
            messages.error(request, "İşlem sırasında bir hata oluştu.")
        return redirect('admin_patients')

    # Verileri Hazırla
    patients = User.objects.filter(is_psychologist=False, is_superuser=False)
    psychologists = User.objects.filter(is_psychologist=True, is_active=True)

    patient_stats = []
    for p in patients:
        logs = ListeningLog.objects.filter(user=p)
        # Toplam dinleme süresi (saniye -> dakika)
        total_seconds = logs.aggregate(Sum('duration_listened'))['duration_listened__sum'] or 0
        # Kaç farklı günde giriş yapmış
        total_days = logs.values('date').distinct().count()
        # Son giriş tarihleri
        last_login_days = logs.order_by('-date').values_list('date', flat=True)[:5]
        
        patient_stats.append({
            'user': p,
            'total_minutes': round(total_seconds / 60, 1),
            'total_days': total_days,
            'history': last_login_days
        })

    return render(request, 'dashboard/admin_patients.html', {
        'patient_stats': patient_stats,
        'psychologists': psychologists
    })

@login_required
def admin_psychologists_view(request):
    """Psikolog Performans Takibi"""
    if not request.user.is_superuser:
        return redirect('landing')

    psychologists = User.objects.filter(is_psychologist=True, is_active=True)
    
    psy_data = []
    for psy in psychologists:
        # Bu psikoloğa atanmış hastaları bul
        my_patients = User.objects.filter(assigned_psychologist=psy)
        patient_list = []
        
        for pat in my_patients:
            # Hastanın son reçetesini bul
            last_pres = Prescription.objects.filter(patient=pat).order_by('-created_at').first()
            patient_list.append({
                'name': f"{pat.first_name} {pat.last_name}",
                'username': pat.username,
                'last_prescription': last_pres
            })
            
        psy_data.append({
            'user': psy,
            'patients': patient_list
        })

    return render(request, 'dashboard/admin_psychologists.html', {'psy_data': psy_data})

@login_required
def send_verification_code(request, user_id):
    """Psikolog onayı için kod üretir ve gönderir"""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Yetkisiz işlem'}, status=403)
        
    try:
        user = User.objects.get(id=user_id)
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        user.verification_code = code
        user.save()
        
        # Geliştirme ortamı için terminale yazdır
        print(f"\n=== ONAY KODU: {code} ===\n")
        
        # E-posta gönder (Hata verirse durmaz, terminaldeki kod kullanılır)
        send_mail(
            'NeuroSound Onay Kodu',
            f'Hesap onay kodunuz: {code}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=True
        )
        return JsonResponse({'status': 'success', 'message': 'Onay kodu oluşturuldu (Terminale bakınız).'})
        
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def approve_psychologist(request):
    """Kodu doğrular ve psikoloğu aktifleştirir"""
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('landing')
        
    user_id = request.POST.get('user_id')
    code_entered = request.POST.get('code')
    
    try:
        user = User.objects.get(id=user_id)
        if user.verification_code == code_entered:
            user.is_active = True
            user.verification_code = None
            user.save()
            messages.success(request, f"{user.first_name} {user.last_name} hesabı onaylandı.")
        else:
            messages.error(request, "Hatalı onay kodu!")
    except User.DoesNotExist:
        messages.error(request, "Kullanıcı bulunamadı.")
        
    return redirect('super_admin_dashboard')

# YENİ: KULLANICI SİLME (SÜPER YÖNETİCİ İÇİN)
@login_required
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('landing')
    
    user = get_object_or_404(User, id=user_id)
    
    # Süper yönetici kendini yanlışlıkla silmesin
    if user.id == request.user.id:
        messages.error(request, "Yönetici hesabınızı buradan silemezsiniz.")
        return redirect('super_admin_dashboard')

    is_psy = user.is_psychologist
    is_active = user.is_active
    name = f"{user.first_name} {user.last_name}"

    user.delete()
    messages.success(request, f"{name} adlı kullanıcı ve tüm verileri başarıyla silindi.")

    # Silinen kullanıcının türüne göre doğru sayfaya geri dön
    if is_psy:
        if not is_active:
            return redirect('super_admin_dashboard') # Onay bekleyenler sayfasına dön
        return redirect('admin_psychologists') # Psikologlar sayfasına dön
    
    return redirect('admin_patients') # Danışanlar sayfasına dön


# --- PSİKOLOG PANELİ ---

@login_required
def psychologist_dashboard(request):
    if not request.user.is_psychologist:
        if request.user.is_superuser:
            return redirect('super_admin_dashboard')
        return redirect('patient_dashboard')

    # YALNIZCA KENDİSİNE ATANMIŞ HASTALARI GÖRÜR
    patients = User.objects.filter(assigned_psychologist=request.user)
    
    # GÜNCELLEME: Psikoloğun atadığı tüm reçeteleri getir (Yeniden eskiye)
    prescriptions = Prescription.objects.filter(assigned_by=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        frequency = request.POST.get('frequency')
        duration = request.POST.get('duration')
        days = request.POST.get('days')
        notes = request.POST.get('notes')

        try:
            # Güvenlik Kontrolü: Reçete yazılmak istenen hasta bu doktora mı ait?
            patient = User.objects.get(id=patient_id, assigned_psychologist=request.user)
            
            Prescription.objects.create(
                patient=patient,
                assigned_by=request.user,
                frequency=frequency,
                duration_minutes=int(duration),
                total_days=int(days),
                notes=notes
            )
            messages.success(request, "Reçete başarıyla oluşturuldu.")
        except User.DoesNotExist:
            messages.error(request, "Hata: Bu hasta size atanmamış veya bulunamadı.")
            
        return redirect('psychologist_dashboard')

    return render(request, 'dashboard/psychologist_dashboard.html', {
        'patients': patients,
        'prescriptions': prescriptions
    })

# Reçete Silme Fonksiyonu
@login_required
def delete_prescription(request, pres_id):
    if not request.user.is_psychologist:
        return redirect('landing')
        
    # Sadece kendi atadığı reçeteyi silebilir
    prescription = get_object_or_404(Prescription, id=pres_id, assigned_by=request.user)
    
    patient_name = prescription.patient.first_name 
    prescription.delete()
    
    messages.warning(request, f"{patient_name} adlı danışanın reçetesi silindi.")
    return redirect('psychologist_dashboard')


# --- MÜZİK KÜTÜPHANESİ ---

@login_required
def music_library(request):
    tracks = [
        {'id': 'rain', 'title': 'Yağmur Sesi', 'desc': 'Hafif yağmur ve gök gürültüsü', 'icon': 'fa-cloud-rain', 'color': 'from-blue-400 to-blue-600', 'file': 'yagmur.mp3'},
        {'id': 'forest', 'title': 'Orman Ambiyansı', 'desc': 'Kuş sesleri ve rüzgar', 'icon': 'fa-tree', 'color': 'from-emerald-400 to-emerald-600', 'file': 'orman.mp3'},
        {'id': 'ocean', 'title': 'Okyanus Dalgaları', 'desc': 'Derin ve ritmik dalgalar', 'icon': 'fa-water', 'color': 'from-cyan-400 to-blue-500', 'file': 'okyanus.mp3'},
        {'id': 'zen', 'title': 'Zen Bahçesi', 'desc': 'Meditatif ve sakinleştirici', 'icon': 'fa-om', 'color': 'from-violet-400 to-purple-600', 'file': 'zenbahcesi.mp3'},
    ]
    return render(request, 'pages/music_library.html', {'tracks': tracks})


# --- DANIŞAN PANELİ ---

@login_required
def patient_dashboard(request):
    if request.user.is_psychologist:
        return redirect('psychologist_dashboard')
    if request.user.is_superuser:
        return redirect('super_admin_dashboard')
    
    # Tüm reçeteleri getir (Seçim için)
    all_prescriptions = Prescription.objects.filter(patient=request.user).order_by('-created_at')
    
    # URL'den veya varsayılan olarak reçete seç
    selected_pres_id = request.GET.get('pres_id')
    prescription = None
    
    if selected_pres_id:
        prescription = all_prescriptions.filter(id=selected_pres_id).first()
    
    if not prescription:
        prescription = all_prescriptions.first()

    today_log, created = ListeningLog.objects.get_or_create(
        user=request.user,
        date=timezone.now().date()
    )
    
    history = ListeningLog.objects.filter(user=request.user).order_by('-date')

    selected_music = request.GET.get('bg_music', None)
    music_title = request.GET.get('title', 'Sessiz Mod')

    return render(request, 'dashboard/patient_dashboard.html', {
        'prescription': prescription,
        'all_prescriptions': all_prescriptions,
        'today_log': today_log,
        'history': history,
        'selected_music': selected_music,
        'music_title': music_title
    })


# --- LOG KAYDETME API ---

@csrf_exempt
@login_required
def save_progress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            completed = data.get('completed', False)
            duration = data.get('duration', 0)
            pres_id = data.get('prescription_id')

            log, created = ListeningLog.objects.get_or_create(
                user=request.user,
                date=timezone.now().date()
            )
            
            log.duration_listened = duration
            
            if completed:
                log.is_completed = True
            
            target_prescription = None
            if pres_id:
                target_prescription = Prescription.objects.filter(id=pres_id, patient=request.user).first()
            
            # ID yoksa en sonuncuyu al (Fallback)
            if not target_prescription:
                target_prescription = Prescription.objects.filter(patient=request.user).order_by('-created_at').first()
                
            if target_prescription:
                log.frequency = target_prescription.frequency
                
            log.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'fail'})