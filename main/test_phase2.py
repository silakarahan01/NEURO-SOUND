"""
Faz 2'de eklenen view'lar için pytest-tabanlı testler.

Mevcut main/tests.py (Django TestCase) korunur; bu dosya yalnızca
yeni eklenen aşağıdaki davranışları doğrular:

- prescription_update_view (edit)
- verify_email_view (e-posta kodu doğrulama)
- create_notification helper
- mark_notification_read / mark_all_notifications_read endpoint'leri
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from main.models import Notification, Prescription, User
from main.utils import (
    create_notification,
    issue_verification_code,
    verification_code_is_valid,
)


# ─── Prescription edit ───────────────────────────────────────────


@pytest.mark.django_db
class TestPrescriptionUpdate:
    def test_psychologist_can_edit_own_prescription(self, authed_psychologist_client, prescription):
        url = reverse('prescription_update', args=[prescription.id])
        response = authed_psychologist_client.post(url, {
            'patient': prescription.patient.id,
            'frequency': 'beta',
            'duration_minutes': 25,
            'total_days': 21,
            'notes': 'Güncellendi',
        })
        assert response.status_code == 302
        prescription.refresh_from_db()
        assert prescription.frequency == 'beta'
        assert prescription.duration_minutes == 25
        assert prescription.total_days == 21
        assert prescription.notes == 'Güncellendi'

    def test_psychologist_cannot_edit_someone_elses_prescription(
        self, client, prescription, django_user_model,
    ):
        other_psy = django_user_model.objects.create_user(
            username='other_psy', email='o@x.com', password='X12345678',
            is_psychologist=True, is_active=True,
        )
        session = client.session
        session['_sub_active'] = True
        session.save()
        client.force_login(other_psy)

        url = reverse('prescription_update', args=[prescription.id])
        response = client.post(url, {
            'patient': prescription.patient.id,
            'frequency': 'gamma',
            'duration_minutes': 10,
            'total_days': 7,
        })
        # Başka psikoloğun reçetesi 404 olmalı
        assert response.status_code == 404

    def test_invalid_form_keeps_user_on_edit_page(
        self, authed_psychologist_client, prescription,
    ):
        url = reverse('prescription_update', args=[prescription.id])
        response = authed_psychologist_client.post(url, {
            'patient': prescription.patient.id,
            'frequency': 'alpha',
            'duration_minutes': 0,        # min 1 → invalid
            'total_days': 14,
        })
        assert response.status_code == 200  # render edildi, redirect değil
        prescription.refresh_from_db()
        assert prescription.duration_minutes == 20  # değişmedi


# ─── E-posta doğrulama ──────────────────────────────────────────


@pytest.mark.django_db
class TestVerifyEmail:
    def test_register_creates_inactive_user_and_sends_code(self, client, mailoutbox):
        response = client.post(reverse('register'), {
            'first_name': 'Yeni',
            'last_name': 'Kullanıcı',
            'username': 'yenikullanici',
            'email': 'yeni@example.com',
            'password': 'GuvenliSifre123',
            'password2': 'GuvenliSifre123',
            'role': 'individual',
            'legal_accepted': 'on',
        })
        assert response.status_code == 302
        assert response.url == reverse('verify_email')

        user = User.objects.get(username='yenikullanici')
        assert user.is_active is False
        assert user.verification_code is not None
        assert len(user.verification_code) == 6

        # E-posta gönderildi mi?
        assert len(mailoutbox) == 1
        assert user.email in mailoutbox[0].to

    def test_correct_code_activates_individual_user(self, client, individual_user):
        individual_user.is_active = False
        individual_user.save(update_fields=['is_active'])
        code = issue_verification_code(individual_user)

        session = client.session
        session['pending_verification_user_id'] = individual_user.id
        session.save()

        response = client.post(reverse('verify_email'), {'code': code})
        assert response.status_code == 302

        individual_user.refresh_from_db()
        assert individual_user.is_active is True
        assert individual_user.verification_code is None

    def test_wrong_code_does_not_activate(self, client, individual_user):
        individual_user.is_active = False
        individual_user.save(update_fields=['is_active'])
        issue_verification_code(individual_user)

        session = client.session
        session['pending_verification_user_id'] = individual_user.id
        session.save()

        response = client.post(reverse('verify_email'), {'code': '999999'})
        assert response.status_code == 200  # form sayfası tekrar render
        individual_user.refresh_from_db()
        assert individual_user.is_active is False

    def test_expired_code_rejected(self, individual_user):
        code = issue_verification_code(individual_user)
        # Süreyi geçmişe al
        individual_user.verification_code_expires_at = timezone.now() - timedelta(minutes=1)
        individual_user.save(update_fields=['verification_code_expires_at'])

        ok, error = verification_code_is_valid(individual_user, code)
        assert ok is False
        assert 'süresi' in error.lower()

    def test_psychologist_email_verified_but_remains_inactive(self, client, mailoutbox):
        """Psikolog kayıt → kod doğru → e-posta verified ama is_active hâlâ False
        (admin onayını ayrıca bekler)."""
        client.post(reverse('register'), {
            'first_name': 'Dr', 'last_name': 'Test',
            'username': 'drtest', 'email': 'dr@example.com',
            'password': 'GuvenliSifre123', 'password2': 'GuvenliSifre123',
            'role': 'psychologist', 'legal_accepted': 'on',
        })
        psy = User.objects.get(username='drtest')
        code = psy.verification_code

        response = client.post(reverse('verify_email'), {'code': code})
        assert response.status_code == 302
        psy.refresh_from_db()
        assert psy.verification_code is None
        assert psy.is_active is False  # admin onayı hâlâ bekliyor


# ─── Notification helper & endpoint'leri ────────────────────────


@pytest.mark.django_db
class TestNotifications:
    def test_create_notification_persists_record(self, patient):
        notif = create_notification(patient, 'Test mesajı', link_url='/x/')
        assert notif is not None
        assert notif.user == patient
        assert notif.message == 'Test mesajı'
        assert notif.is_read is False

    def test_create_notification_truncates_long_message(self, patient):
        long_msg = 'x' * 500
        notif = create_notification(patient, long_msg)
        assert len(notif.message) == 255

    def test_create_notification_skips_when_args_missing(self, patient):
        assert create_notification(None, 'msg') is None
        assert create_notification(patient, '') is None

    def test_mark_single_notification_read(self, authed_client, patient):
        n = Notification.objects.create(user=patient, message='Hi')
        url = reverse('notification_mark_read', args=[n.id])
        response = authed_client.post(url)
        assert response.status_code == 200
        n.refresh_from_db()
        assert n.is_read is True

    def test_cannot_mark_other_users_notification(self, authed_client, individual_user):
        other_notif = Notification.objects.create(user=individual_user, message='gizli')
        url = reverse('notification_mark_read', args=[other_notif.id])
        response = authed_client.post(url)
        assert response.status_code == 200
        # Update sayısı 0 olmalı (queryset farklı user'la filter ettiği için)
        other_notif.refresh_from_db()
        assert other_notif.is_read is False

    def test_mark_all_notifications_read(self, authed_client, patient):
        for i in range(3):
            Notification.objects.create(user=patient, message=f'm{i}')
        response = authed_client.post(reverse('notification_mark_all_read'))
        assert response.status_code == 200
        unread = Notification.objects.filter(user=patient, is_read=False).count()
        assert unread == 0

    def test_prescription_creation_notifies_patient(
        self, authed_psychologist_client, patient,
    ):
        url = reverse('psychologist_dashboard')
        authed_psychologist_client.post(url, {
            'patient_id': patient.id,
            'frequency': 'theta',
            'duration': 30,
            'days': 14,
            'notes': 'Bildirim testi',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        assert Prescription.objects.filter(patient=patient).count() == 1
        assert Notification.objects.filter(user=patient).count() == 1
