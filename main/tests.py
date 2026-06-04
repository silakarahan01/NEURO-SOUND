import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import User, Prescription, ListeningLog, SubscriptionPlan, UserSubscription, ContactMessage


def make_superuser(**kw):
    d = dict(username='superadmin', password='Admin123!', email='admin@test.com')
    d.update(kw)
    return User.objects.create_superuser(**d)


def make_psychologist(**kw):
    d = dict(username='psikolog1', password='Psiko123!', is_psychologist=True, is_active=True)
    d.update(kw)
    pw = d.pop('password')
    u = User(**d)
    u.set_password(pw)
    u.save()
    return u


def make_patient(**kw):
    d = dict(username='hasta1', password='Hasta123!', is_psychologist=False, is_individual=False)
    d.update(kw)
    pw = d.pop('password')
    u = User(**d)
    u.set_password(pw)
    u.save()
    return u


def activate_subscription(user, days=30):
    plan, _ = SubscriptionPlan.objects.get_or_create(
        name='PSYCHOLOGIST' if user.is_psychologist else 'INDIVIDUAL',
        defaults={'price': 500.00 if user.is_psychologist else 50.00}
    )
    return UserSubscription.objects.create(
        user=user, plan=plan,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=days),
        is_active=True,
    )


# --- Model Testleri ---

class UserModelTest(TestCase):
    def test_patient_role_display(self):
        u = User(username='h', is_psychologist=False, is_individual=False)
        self.assertEqual(u.get_role_display(), 'Danışan')

    def test_psychologist_role_display(self):
        u = User(username='p', is_psychologist=True)
        self.assertEqual(u.get_role_display(), 'Psikolog')

    def test_individual_role_display(self):
        u = User(username='b', is_individual=True)
        self.assertEqual(u.get_role_display(), 'Bireysel Kullanıcı')

    def test_superuser_role_display(self):
        u = User(username='a', is_superuser=True)
        self.assertEqual(u.get_role_display(), 'Süper Yönetici')

    def test_cannot_be_both_psychologist_and_individual(self):
        from django.core.exceptions import ValidationError
        u = User(username='c', is_psychologist=True, is_individual=True)
        with self.assertRaises(ValidationError):
            u.clean()

    def test_user_str(self):
        u = User(username='test', is_psychologist=True)
        self.assertIn('test', str(u))


class ListeningLogTest(TestCase):
    def setUp(self):
        self.patient = make_patient(username='log_hasta')

    def test_log_created_for_today(self):
        log, created = ListeningLog.objects.get_or_create(
            user=self.patient, date=timezone.now().date())
        self.assertTrue(created)
        self.assertEqual(log.duration_listened, 0)

    def test_unique_log_per_user_per_day(self):
        from django.db import IntegrityError
        today = timezone.now().date()
        ListeningLog.objects.create(user=self.patient, date=today)
        with self.assertRaises(IntegrityError):
            ListeningLog.objects.create(user=self.patient, date=today)


# --- Auth View Testleri ---

class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = make_patient(username='auth_hasta')
        activate_subscription(self.patient)
        self.psychologist = make_psychologist(username='auth_psiko')
        activate_subscription(self.psychologist)
        self.superuser = make_superuser(username='auth_super')

    def test_login_page_loads(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_register_page_loads(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def test_patient_login_redirects_to_dashboard(self):
        r = self.client.post(reverse('login'), {'username': 'auth_hasta', 'password': 'Hasta123!'})
        self.assertRedirects(r, reverse('patient_dashboard'))

    def test_psychologist_login_redirects_to_dashboard(self):
        r = self.client.post(reverse('login'), {'username': 'auth_psiko', 'password': 'Psiko123!'})
        self.assertRedirects(r, reverse('psychologist_dashboard'))

    def test_superuser_login_redirects_to_admin(self):
        r = self.client.post(reverse('login'), {'username': 'auth_super', 'password': 'Admin123!'})
        self.assertRedirects(r, reverse('super_admin_dashboard'))

    def test_invalid_login_returns_form(self):
        r = self.client.post(reverse('login'), {'username': 'auth_hasta', 'password': 'yanlis'})
        self.assertEqual(r.status_code, 200)

    def test_unauthenticated_dashboard_redirects(self):
        r = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_logout_clears_session(self):
        self.client.login(username='auth_hasta', password='Hasta123!')
        self.client.get(reverse('logout'))
        r = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_patient_cannot_access_psychologist_dashboard(self):
        self.client.login(username='auth_hasta', password='Hasta123!')
        self.assertRedirects(
            self.client.get(reverse('psychologist_dashboard')), reverse('patient_dashboard'))

    def test_psychologist_cannot_access_patient_dashboard(self):
        self.client.login(username='auth_psiko', password='Psiko123!')
        self.assertRedirects(
            self.client.get(reverse('patient_dashboard')), reverse('psychologist_dashboard'))


# --- Abonelik Middleware ---

class SubscriptionMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = make_patient(username='mid_hasta')
        self.superuser = make_superuser(username='mid_super')

    def test_landing_accessible_without_subscription(self):
        self.client.login(username='mid_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('landing')).status_code, 200)

    def test_no_subscription_redirects_to_payment(self):
        self.client.login(username='mid_hasta', password='Hasta123!')
        self.assertRedirects(self.client.get(reverse('patient_dashboard')), reverse('payment_view'))

    def test_active_subscription_allows_access(self):
        activate_subscription(self.patient)
        self.client.login(username='mid_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('patient_dashboard')).status_code, 200)

    def test_expired_subscription_redirects_to_payment(self):
        plan, _ = SubscriptionPlan.objects.get_or_create(name='INDIVIDUAL', defaults={'price': 50})
        UserSubscription.objects.create(
            user=self.patient, plan=plan,
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() - timedelta(days=30),
            is_active=True,
        )
        self.client.login(username='mid_hasta', password='Hasta123!')
        self.assertRedirects(self.client.get(reverse('patient_dashboard')), reverse('payment_view'))

    def test_superuser_bypasses_subscription(self):
        self.client.login(username='mid_super', password='Admin123!')
        self.assertEqual(self.client.get(reverse('super_admin_dashboard')).status_code, 200)


# --- Super Admin ---

class SuperAdminViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser(username='sadmin')
        self.patient = make_patient(username='sadmin_hasta')
        activate_subscription(self.patient)

    def test_non_superuser_redirected_from_admin(self):
        self.client.login(username='sadmin_hasta', password='Hasta123!')
        self.assertRedirects(self.client.get(reverse('super_admin_dashboard')), reverse('landing'))

    def test_superuser_can_access_dashboard(self):
        self.client.login(username='sadmin', password='Admin123!')
        self.assertEqual(self.client.get(reverse('super_admin_dashboard')).status_code, 200)

    def test_superuser_cannot_delete_self(self):
        self.client.login(username='sadmin', password='Admin123!')
        self.client.post(reverse('delete_user', args=[self.superuser.id]))
        self.assertTrue(User.objects.filter(id=self.superuser.id).exists())

    def test_superuser_can_delete_patient(self):
        self.client.login(username='sadmin', password='Admin123!')
        pid = self.patient.id
        self.client.post(reverse('delete_user', args=[pid]))
        self.assertFalse(User.objects.filter(id=pid).exists())


# --- Psikolog ---

class PsychologistViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.psy = make_psychologist(username='psy_v')
        activate_subscription(self.psy)
        self.psy2 = make_psychologist(username='psy_v2')
        activate_subscription(self.psy2)
        self.patient = make_patient(username='psy_hasta', assigned_psychologist=self.psy)
        activate_subscription(self.patient)

    def test_create_prescription(self):
        self.client.login(username='psy_v', password='Psiko123!')
        self.client.post(reverse('psychologist_dashboard'), {
            'patient_id': self.patient.id, 'frequency': 'Alpha',
            'duration': '20', 'days': '14', 'notes': 'Test',
        })
        self.assertTrue(Prescription.objects.filter(patient=self.patient, frequency='Alpha').exists())

    def test_cannot_create_prescription_for_unassigned_patient(self):
        other = make_patient(username='oph', assigned_psychologist=self.psy2)
        self.client.login(username='psy_v', password='Psiko123!')
        self.client.post(reverse('psychologist_dashboard'), {
            'patient_id': other.id, 'frequency': 'Beta',
            'duration': '15', 'days': '10', 'notes': '',
        })
        self.assertFalse(Prescription.objects.filter(patient=other, assigned_by=self.psy).exists())

    def test_delete_own_prescription(self):
        pres = Prescription.objects.create(
            patient=self.patient, assigned_by=self.psy,
            frequency='Gamma', duration_minutes=15, total_days=7)
        self.client.login(username='psy_v', password='Psiko123!')
        self.client.post(reverse('delete_prescription', args=[pres.id]))
        self.assertFalse(Prescription.objects.filter(id=pres.id).exists())

    def test_cannot_delete_other_psychologists_prescription(self):
        other = make_patient(username='op3', assigned_psychologist=self.psy2)
        pres = Prescription.objects.create(
            patient=other, assigned_by=self.psy2,
            frequency='Theta', duration_minutes=10, total_days=5)
        self.client.login(username='psy_v', password='Psiko123!')
        r = self.client.post(reverse('delete_prescription', args=[pres.id]))
        self.assertEqual(r.status_code, 404)


# --- API ---

class SaveProgressAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = make_patient(username='api_hasta')
        activate_subscription(self.patient)
        self.psy = make_psychologist(username='api_psiko')
        self.pres = Prescription.objects.create(
            patient=self.patient, assigned_by=self.psy,
            frequency='Alpha', duration_minutes=15, total_days=7)

    def _post(self, payload):
        return self.client.post(
            reverse('save_progress'),
            data=json.dumps(payload),
            content_type='application/json')

    def test_requires_post_method(self):
        self.client.login(username='api_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('save_progress')).status_code, 405)

    def test_requires_authentication(self):
        self.assertEqual(self._post({'duration': 60}).status_code, 302)

    def test_saves_listening_log(self):
        self.client.login(username='api_hasta', password='Hasta123!')
        r = self._post({'duration': 900, 'completed': False, 'prescription_id': self.pres.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['status'], 'success')
        log = ListeningLog.objects.get(user=self.patient, date=timezone.now().date())
        self.assertEqual(log.duration_listened, 900)

    def test_marks_completed(self):
        self.client.login(username='api_hasta', password='Hasta123!')
        self._post({'duration': 1800, 'completed': True, 'prescription_id': self.pres.id})
        log = ListeningLog.objects.get(user=self.patient, date=timezone.now().date())
        self.assertTrue(log.is_completed)

    def test_invalid_json_returns_400(self):
        self.client.login(username='api_hasta', password='Hasta123!')
        r = self.client.post(
            reverse('save_progress'), data='bad', content_type='application/json')
        self.assertEqual(r.status_code, 400)


# --- Iletisim ---

class ContactFormTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_contact_page_loads(self):
        self.assertEqual(self.client.get(reverse('contact')).status_code, 200)

    def test_contact_requires_all_fields(self):
        self.client.post(reverse('contact'), {
            'name': 'T', 'email': '', 'message': 'M', 'data_consent': 'on'})
        self.assertFalse(ContactMessage.objects.exists())

    def test_contact_requires_data_consent(self):
        self.client.post(reverse('contact'), {
            'name': 'T', 'email': 't@t.com', 'message': 'M'})
        self.assertFalse(ContactMessage.objects.exists())

    def test_contact_saves_message(self):
        self.client.post(reverse('contact'), {
            'name': 'User', 'email': 'u@test.com',
            'message': 'Test mesaj', 'data_consent': 'on'})
        self.assertTrue(ContactMessage.objects.filter(email='u@test.com').exists())


# --- Kayit Formu ---

class RegistrationFormTest(TestCase):
    def _reg(self, **kw):
        d = {'first_name': 'Ad', 'last_name': 'Soyad',
             'username': 'regtest1', 'email': 'reg@test.com',
             'password': 'Guclu123!', 'role': 'patient', 'legal_accepted': 'on'}
        d.update(kw)
        return self.client.post(reverse('register'), d)

    def test_valid_registration_redirects(self):
        self.assertRedirects(self._reg(), reverse('payment_view'))

    def test_short_password_fails(self):
        r = self._reg(password='123')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='regtest1').exists())

    def test_legal_not_accepted_fails(self):
        r = self.client.post(reverse('register'), {
            'first_name': 'A', 'last_name': 'B',
            'username': 'nolegal', 'email': 'nl@test.com',
            'password': 'Guclu123!', 'role': 'patient'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='nolegal').exists())


# --- Profil, Odeme ve Muzik Kutuphanesi ---

class ProfilePaymentMusicTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = make_patient(username='ppm_hasta')
        activate_subscription(self.patient)
        self.psychologist = make_psychologist(username='ppm_psiko')
        activate_subscription(self.psychologist)

    def test_profile_page_loads_for_patient(self):
        self.client.login(username='ppm_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('profile_view')).status_code, 200)

    def test_profile_page_loads_for_psychologist(self):
        self.client.login(username='ppm_psiko', password='Psiko123!')
        self.assertEqual(self.client.get(reverse('profile_view')).status_code, 200)

    def test_profile_requires_login(self):
        self.assertEqual(self.client.get(reverse('profile_view')).status_code, 302)

    def test_payment_page_loads(self):
        self.client.login(username='ppm_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('payment_view')).status_code, 200)

    def test_payment_creates_subscription(self):
        new_patient = make_patient(username='pay_hasta2')
        self.client.login(username='pay_hasta2', password='Hasta123!')
        self.client.post(reverse('payment_view'))
        self.assertTrue(
            UserSubscription.objects.filter(user=new_patient, is_active=True).exists()
        )

    def test_payment_redirects_patient_to_dashboard(self):
        self.client.login(username='ppm_hasta', password='Hasta123!')
        self.assertRedirects(
            self.client.post(reverse('payment_view')), reverse('patient_dashboard')
        )

    def test_music_library_loads(self):
        self.client.login(username='ppm_hasta', password='Hasta123!')
        self.assertEqual(self.client.get(reverse('music_library')).status_code, 200)

    def test_music_library_requires_login(self):
        self.assertEqual(self.client.get(reverse('music_library')).status_code, 302)
