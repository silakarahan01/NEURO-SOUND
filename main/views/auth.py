import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from ..forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from ..models import User, UserSubscription
from ..utils import (
    get_subscription_info,
    issue_verification_code,
    verification_code_is_valid,
)

logger = logging.getLogger('main')

PENDING_VERIFICATION_KEY = 'pending_verification_user_id'


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """Giriş işlemi. Role göre yönlendirme yapar."""
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
            logger.info(f"Başarılı giriş: {user.username}")

            # Check for next URL (deep link from @login_required redirect)
            next_url = request.GET.get('next')

            if user.is_superuser:
                return redirect(next_url or 'super_admin_dashboard')

            today = timezone.now().date()
            active_sub = UserSubscription.objects.filter(
                user=user, is_active=True, end_date__gte=today
            ).exists()

            if not active_sub:
                return redirect('payment_view')

            if user.is_psychologist:
                return redirect(next_url or 'psychologist_dashboard')
            return redirect(next_url or 'patient_dashboard')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def register_view(request):
    """Kayıt işlemi. Tüm yeni kullanıcılar e-posta doğrulama akışına yönlendirilir.

    - Hasta/Bireysel: doğrulama tamamlanınca is_active=True ve otomatik login.
    - Psikolog: doğrulama tamamlanınca is_active hâlâ False kalır (admin onayını
      ayrı olarak bekler).
    """
    if request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        if not request.POST.get('legal_accepted'):
            form = UserRegistrationForm(request.POST)
            return render(request, 'accounts/register.html', {
                'form': form,
                'error': 'Kayıt olmak için sözleşmeleri kabul etmeniz zorunludur.'
            })

        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"Yeni kayıt: {user.username} (rol: {user.get_role_display()})")

            issue_verification_code(user)
            request.session[PENDING_VERIFICATION_KEY] = user.id
            messages.info(
                request,
                "E-posta adresinize 6 haneli doğrulama kodu gönderildi. "
                "Hesabınızı etkinleştirmek için lütfen kodu girin."
            )
            return redirect('verify_email')

        error_message = list(form.errors.values())[0][0] if form.errors else None
        return render(request, 'accounts/register.html', {'form': form, 'error': error_message})

    form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def verify_email_view(request):
    """Kayıt sonrası 6 haneli kod doğrulama ekranı."""
    user_id = request.session.get(PENDING_VERIFICATION_KEY)
    if not user_id:
        messages.error(request, "Doğrulama oturumu bulunamadı. Lütfen tekrar kayıt olun.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop(PENDING_VERIFICATION_KEY, None)
        return redirect('register')

    if request.method == 'POST':
        entered = (request.POST.get('code') or '').strip()
        is_valid, error = verification_code_is_valid(user, entered)
        if not is_valid:
            messages.error(request, error)
            return render(request, 'accounts/verify_email.html', {'email': user.email})

        # Kod doğru; alanları temizle
        user.verification_code = None
        user.verification_code_expires_at = None

        if user.is_psychologist:
            # Psikolog: e-posta doğrulandı ama admin onayı hâlâ gerekli
            user.save(update_fields=['verification_code', 'verification_code_expires_at'])
            request.session.pop(PENDING_VERIFICATION_KEY, None)
            messages.success(
                request,
                "E-posta adresiniz doğrulandı. Psikolog hesabınız yönetici onayından "
                "sonra aktifleşecektir."
            )
            return redirect('login')

        # Hasta / Bireysel: hesabı aktive et ve oturum aç
        user.is_active = True
        user.save(update_fields=[
            'is_active', 'verification_code', 'verification_code_expires_at',
        ])
        request.session.pop(PENDING_VERIFICATION_KEY, None)
        login(request, user)
        logger.info("E-posta doğrulandı ve aktif: %s", user.username)
        messages.success(request, "Hesabınız etkinleştirildi! Lütfen abonelik satın alın.")
        return redirect('payment_view')

    return render(request, 'accounts/verify_email.html', {'email': user.email})


@require_POST
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def resend_verification_view(request):
    """Süresi dolan kullanıcı yeni bir doğrulama kodu ister."""
    user_id = request.session.get(PENDING_VERIFICATION_KEY)
    if not user_id:
        messages.error(request, "Doğrulama oturumu bulunamadı.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop(PENDING_VERIFICATION_KEY, None)
        return redirect('register')

    issue_verification_code(user)
    messages.info(request, "Yeni doğrulama kodu e-postanıza gönderildi.")
    return redirect('verify_email')


@require_POST
def logout_view(request):
    """Çıkış işlemi. POST only for CSRF protection."""
    logout(request)
    messages.success(request, "Çıkış işlemi başarıyla gerçekleştirildi.")
    return redirect('login')


@login_required
def profile_view(request):
    """Kullanıcı profili: bilgi güncelleme ve şifre değiştirme."""
    user_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserProfileForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profil bilgileriniz güncellendi.')
                return redirect('profile_view')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Şifreniz başarıyla değiştirildi.')
                return redirect('profile_view')
            else:
                messages.error(request, 'Şifre değiştirme hatası. Lütfen bilgileri kontrol edin.')

    formatted_start = "-"
    formatted_end = "-"
    try:
        subscription = request.user.usersubscription_set.filter(is_active=True).latest('created_at')
        if subscription.start_date:
            formatted_start = subscription.start_date.strftime('%d.%m.%Y')
        if subscription.end_date:
            formatted_end = subscription.end_date.strftime('%d.%m.%Y')
    except UserSubscription.DoesNotExist:
        subscription = None

    return render(request, 'dashboard/profile.html', {
        'user_form': user_form,
        'password_form': password_form,
        'subscription': subscription,
        'formatted_start': formatted_start,
        'formatted_end': formatted_end,
    })
