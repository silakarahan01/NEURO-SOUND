from django.urls import path
from django.contrib.auth import views as auth_views
from main import views

urlpatterns = [
    # ─── Ana Sayfalar ──────────────────────────────────────────
    path('', views.landing_view, name='landing'),
    path('cookie-policy/', views.cookie_policy_view, name='cookie_policy'),
    path('frequencies/', views.frequency_info_view, name='frequency_info'),

    # ─── Yasal Sayfalar ────────────────────────────────────────
    path('kvkk/', views.kvkk_view, name='kvkk'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),

    # ─── Kimlik Doğrulama ──────────────────────────────────────
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('verify-email/resend/', views.resend_verification_view, name='resend_verification'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile_view'),

    # ─── Şifre Sıfırlama ───────────────────────────────────────
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),

    # ─── Süper Yönetici Paneli ─────────────────────────────────
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/patients/', views.admin_patients_view, name='admin_patients'),
    path('super-admin/patients/<int:patient_id>/', views.admin_patient_detail_view, name='admin_patient_detail'),
    path('super-admin/psychologists/', views.admin_psychologists_view, name='admin_psychologists'),
    path('super-admin/onaylar/', views.admin_onaylar_view, name='admin_onaylar'),
    path('super-admin/formlar/', views.admin_formlar_view, name='admin_formlar'),
    path('super-admin/muzik/', views.admin_muzik_view, name='admin_muzik'),
    path('super-admin/send-code/<int:user_id>/', views.send_verification_code, name='send_verification_code'),
    path('super-admin/approve/', views.approve_psychologist, name='approve_psychologist'),
    path('super-admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('super-admin/mark-message-read/<int:msg_id>/', views.mark_message_read, name='mark_message_read'),

    # ─── Psikolog Paneli ───────────────────────────────────────
    path('psychologist/', views.psychologist_dashboard, name='psychologist_dashboard'),
    path('psychologist/patient/<int:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('psychologist/prescription/<int:pres_id>/edit/', views.prescription_update_view, name='prescription_update'),
    path('psychologist/delete-prescription/<int:pres_id>/', views.delete_prescription, name='delete_prescription'),
    path('psychologist/delete-note/<int:note_id>/', views.delete_session_note_view, name='delete_session_note'),

    # ─── Danışan Paneli ────────────────────────────────────────
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/survey/', views.survey_view, name='survey_view'),
    path('library/', views.music_library, name='music_library'),

    # ─── Abonelik & Ödeme ──────────────────────────────────────
    path('subscription/payment/', views.payment_view, name='payment_view'),

    # ─── API (AJAX) ────────────────────────────────────────────
    path('api/save_progress/', views.save_progress, name='save_progress'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='notification_mark_read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='notification_mark_all_read'),
]
