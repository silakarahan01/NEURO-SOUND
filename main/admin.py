from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Prescription, ListeningLog

# Özelleştirilmiş Kullanıcı Modeli için Admin Ayarları
class CustomUserAdmin(UserAdmin):
    model = User
    # 1. Liste görünümü (Burada sorun yoktu)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_psychologist', 'is_active']
    list_filter = ['is_psychologist', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # 2. EKSİK OLAN KISIM: Düzenleme Sayfası (Edit User)
    # Mevcut UserAdmin alanlarının üzerine senin özel alanlarını ekliyoruz.
    fieldsets = UserAdmin.fieldsets + (
        ('Özel Bilgiler (Proje Bazlı)', {
            'fields': ('is_psychologist', 'verification_code', 'assigned_psychologist'),
        }),
    )
    
    # 3. EKSİK OLAN KISIM: Yeni Kullanıcı Ekleme Sayfası (Add User)
    # Kullanıcı oluştururken bu alanların da sorulmasını sağlar.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Özel Bilgiler (Proje Bazlı)', {
            'fields': ('is_psychologist', 'verification_code', 'assigned_psychologist'),
        }),
    )



# Reçete Modeli için Admin Ayarları
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'assigned_by', 'frequency', 'duration_minutes', 'total_days', 'created_at']
    list_filter = ['frequency', 'created_at']
    search_fields = ['patient__username', 'assigned_by__username']

# Dinleme Günlüğü için Admin Ayarları
class ListeningLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'frequency', 'duration_listened', 'is_completed']
    list_filter = ['is_completed', 'date', 'frequency']
    search_fields = ['user__username']

# Modelleri Admin Paneline Kaydet
admin.site.register(User, CustomUserAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(ListeningLog, ListeningLogAdmin)