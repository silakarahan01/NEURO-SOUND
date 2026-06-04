"""
NEURO SOUND — pytest-django ortak fixture'ları.

Tests dizini: main/  (pytest.ini_options.testpaths)
Bu fixture'lar mevcut Django TestCase'lerden bağımsız çalışır;
yeni testler @pytest.fixture(name='psychologist') gibi kullanır.

Çalıştırma:
    pytest                       # tüm testler
    pytest -k prescription       # filter
    pytest --cov=main            # coverage raporu
"""
from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.fixture
def superuser(db, django_user_model):
    """is_superuser=True yetkili admin."""
    return django_user_model.objects.create_superuser(
        username='superadmin',
        email='admin@neurosound.test',
        password='Adm1nPass!',
    )


@pytest.fixture
def psychologist(db, django_user_model):
    """Aktif, onaylanmış bir psikolog."""
    return django_user_model.objects.create_user(
        username='psy_kemal',
        email='kemal@neurosound.test',
        password='PsyPass123!',
        first_name='Kemal',
        last_name='Yıldız',
        is_psychologist=True,
        is_active=True,
    )


@pytest.fixture
def patient(db, django_user_model, psychologist):
    """psychologist'a atanmış aktif danışan."""
    return django_user_model.objects.create_user(
        username='hasta_ayse',
        email='ayse@neurosound.test',
        password='PatientPass123!',
        first_name='Ayşe',
        last_name='Demir',
        is_active=True,
        assigned_psychologist=psychologist,
    )


@pytest.fixture
def individual_user(db, django_user_model):
    """Bireysel (psikolog atamasız) aktif kullanıcı."""
    return django_user_model.objects.create_user(
        username='bireysel_can',
        email='can@neurosound.test',
        password='IndPass123!',
        first_name='Can',
        last_name='Aslan',
        is_individual=True,
        is_active=True,
    )


@pytest.fixture
def prescription(db, psychologist, patient):
    """psychologist tarafından patient'a atanmış basit reçete."""
    from main.models import Prescription
    return Prescription.objects.create(
        patient=patient,
        assigned_by=psychologist,
        frequency='alpha',
        duration_minutes=20,
        total_days=14,
        notes='Pytest fixture reçetesi',
    )


@pytest.fixture
def active_subscription(db, patient):
    """patient için 30 gün geçerli aktif abonelik."""
    from main.models import SubscriptionPlan, UserSubscription
    plan, _ = SubscriptionPlan.objects.get_or_create(
        name='INDIVIDUAL', defaults={'price': 50.00},
    )
    today = timezone.now().date()
    return UserSubscription.objects.create(
        user=patient,
        plan=plan,
        start_date=today,
        end_date=today + timedelta(days=30),
        is_active=True,
    )


@pytest.fixture
def authed_client(client, patient, active_subscription):
    """Aktif abonelikli bir hastayla giriş yapılmış Django test client'ı."""
    client.force_login(patient)
    return client


@pytest.fixture
def authed_psychologist_client(client, psychologist):
    """Psikolog ile giriş yapılmış client (abonelik yokluğunu middleware halleder)."""
    # SubscriptionMiddleware'in psikoloğu payment'a yönlendirmesini önlemek için
    # session cache flag'ini set ediyoruz; production akışında ödeme view'u
    # bunu doğal olarak set eder.
    session = client.session
    session['_sub_active'] = True
    session.save()
    client.force_login(psychologist)
    return client
