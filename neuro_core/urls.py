from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ANA SAYFALAR ---
    path('/', views.landing_view, name='landing'),
    
    # Giriş ve Kayıt İşlemleri
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- SÜPER YÖNETİCİ (SUPER ADMIN) İŞLEMLERİ ---
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/patients/', views.admin_patients_view, name='admin_patients'),       # Danışan Yönetimi
    path('super-admin/psychologists/', views.admin_psychologists_view, name='admin_psychologists'), # Psikolog Yönetimi
    path('super-admin/send-code/<int:user_id>/', views.send_verification_code, name='send_verification_code'),
    path('super-admin/approve/', views.approve_psychologist, name='approve_psychologist'),

    # --- PSİKOLOG PANELİ & İŞLEMLERİ ---
    path('psychologist/', views.psychologist_dashboard, name='psychologist_dashboard'),
    # YENİ: Reçete silme yolu
    path('psychologist/delete-prescription/<int:pres_id>/', views.delete_prescription, name='delete_prescription'),

    # --- DANIŞAN PANELİ ---
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('library/', views.music_library, name='music_library'), # Müzik Kütüphanesi
    
    # --- API (AJAX İstekleri İçin) ---
    path('api/save_progress/', views.save_progress, name='save_progress'),

    # --- ŞİFRE SIFIRLAMA (GÜNCELLENMİŞ YOLLAR) ---
    # Template yollarını 'accounts/' klasörüne yönlendirdik
    
    # 1. E-posta Girme Sayfası
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), 
         name='password_reset'),

    # 2. E-posta Gönderildi Bilgisi
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),

    # 3. Yeni Şifre Girme Sayfası (Linkteki token ile)
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), 
         name='password_reset_confirm'),

    # 4. İşlem Tamamlandı
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),
     # --- KULLANICI SİLME İŞLEMİ (SÜPER YÖNETİCİ) ---
     path('super-admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]