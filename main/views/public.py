import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django_ratelimit.decorators import ratelimit

from ..models import User, ListeningLog
from ..forms import ContactForm
from ..constants import FREQUENCIES

logger = logging.getLogger('main')


def landing_view(request):
    """Tanıtım (landing) sayfası."""
    user_count = User.objects.filter(is_superuser=False).count()
    session_count = ListeningLog.objects.filter(is_completed=True).count()
    return render(request, 'pages/landing.html', {
        'user_count': user_count,
        'session_count': session_count,
    })


def cookie_policy_view(request):
    return render(request, 'pages/cookie_policy.html')


def frequency_info_view(request):
    """Display frequency information with back navigation."""
    if request.user.is_authenticated and request.user.is_psychologist:
        return redirect('psychologist_dashboard')

    # Determine back URL based on user role
    back_url = request.GET.get('next', '/')
    if request.user.is_authenticated:
        if request.user.is_psychologist:
            back_url = 'psychologist_dashboard'
        else:
            back_url = 'patient_dashboard'

    # Convert frequency constants to list format
    frequencies = [
        {
            'name': freq_data['name'],
            'range': freq_data['frequency'],
            'desc': freq_data['description'],
            'benefits': freq_data['benefits'],
            'icon': freq_data['icon_class'],
            'color': freq_data['color'],
            'tailwind_classes': freq_data['tailwind_classes'],
        }
        for freq_data in FREQUENCIES.values()
    ]

    return render(request, 'frequency_info.html', {
        'frequencies': frequencies,
        'back_url': back_url,
    })


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def contact_view(request):
    """Handle contact form submissions."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            logger.info(f"Yeni iletişim mesajı: {contact_message.name} <{contact_message.email}>")

            # Send notification email
            try:
                send_mail(
                    subject=f'NeuroSound İletişim Formu: {contact_message.name}',
                    message=f'Gönderen: {contact_message.name} <{contact_message.email}>\n\nMesaj:\n{contact_message.message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_CONTACT_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"İletişim e-postası gönderilemedi: {e}")
                messages.warning(request, 'Mesajınız alındı, ancak onay e-postası gönderilemedi.')
                return redirect('contact')

            messages.success(request, 'Mesajınız alındı, en kısa sürede size dönüş yapacağız.')
            return redirect('contact')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def kvkk_view(request):
    return render(request, 'legal/kvkk.html')


def terms_view(request):
    return render(request, 'legal/terms.html')


def privacy_view(request):
    return render(request, 'legal/privacy.html')
