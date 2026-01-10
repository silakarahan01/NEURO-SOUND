from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from main import views # DİKKAT: Uygulama klasörünün adı 'main' ise bu doğru.
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ANA SAYFALAR ---
    # DÜZELTME: '/' yerine '' (boş string) kullanıldı.
    path('', views.landing_view, name='landing'),
    path('cookie-policy/', views.cookie_policy_view, name='cookie_policy'),
    
    # Giriş ve Kayıt İşlemleri
    path('profile/', views.profile_view, name='profile_view'),
    path('frequencies/', views.frequency_info_view, name='frequency_info'),
    
    # Yasal Sayfalar
    path('kvkk/', views.kvkk_view, name='kvkk'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),
    
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- SÜPER YÖNETİCİ (SUPER ADMIN) İŞLEMLERİ ---
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/patients/', views.admin_patients_view, name='admin_patients'),
    path('super-admin/psychologists/', views.admin_psychologists_view, name='admin_psychologists'),
    path('super-admin/send-code/<int:user_id>/', views.send_verification_code, name='send_verification_code'),
    path('super-admin/approve/', views.approve_psychologist, name='approve_psychologist'),
    path('super-admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    # --- PSİKOLOG PANELİ & İŞLEMLERİ ---
    path('psychologist/', views.psychologist_dashboard, name='psychologist_dashboard'),
    path('psychologist/patient/<int:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('psychologist/delete-prescription/<int:pres_id>/', views.delete_prescription, name='delete_prescription'),

    # --- DANIŞAN PANELİ ---
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('library/', views.music_library, name='music_library'),
    
    # --- API (AJAX İstekleri İçin) ---
    path('api/save_progress/', views.save_progress, name='save_progress'),

    # --- ABONELİK VE ÖDEME ---
    path('subscription/payment/', views.payment_view, name='payment_view'),

    # --- ŞİFRE SIFIRLAMA ---
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
]

# EKLEME: Statik ve Medya dosyalarının sunulması (Sadece Debug modunda)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)