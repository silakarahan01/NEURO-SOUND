from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 1. Özelleştirilmiş Kullanıcı Modeli
class User(AbstractUser):
    is_psychologist = models.BooleanField(default=False, verbose_name="Psikolog Mu?")
    
    # Psikolog onayı için gerekli alanlar
    verification_code = models.CharField(max_length=6, blank=True, null=True, verbose_name="Doğrulama Kodu")
    
    # YENİ: HASTA ATAMA SİSTEMİ
    # Bir hasta, bir psikoloğa atanır. Psikolog silinirse hasta silinmez (SET_NULL).
    assigned_psychologist = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='assigned_patients',
        limit_choices_to={'is_psychologist': True},
        verbose_name="Atanmış Psikolog"
    )
    
    description = models.TextField(blank=True, null=True, verbose_name="Hakkında / Notlar")
    psychologist_notes = models.TextField(blank=True, null=True, verbose_name="Psikolog Notları (Özel)")

    def __str__(self):
        role = " (Psikolog)" if self.is_psychologist else " (Danışan)"
        return f"{self.username}{role}"

# 2. Frekans Seçenekleri
FREQUENCY_CHOICES = (
    ('Delta', 'Delta (0.5-4Hz) - Derin Uyku'),
    ('Theta', 'Theta (4-8Hz) - Meditasyon'),
    ('Alpha', 'Alpha (8-13Hz) - Gevşeme'),
    ('Beta', 'Beta (13-30Hz) - Odaklanma'),
    ('Gamma', 'Gamma (30Hz+) - Yüksek Biliş'),
)

# 3. Reçete Modeli
class Prescription(models.Model):
    # Bir hastanın geçmişe dönük birden fazla reçete kaydı olabilir
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions', limit_choices_to={'is_psychologist': False})
    
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_prescriptions', limit_choices_to={'is_psychologist': True})
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    duration_minutes = models.IntegerField(default=15, help_text="Günlük dinleme süresi (dk)")
    total_days = models.IntegerField(default=15, help_text="Kaç gün sürecek?")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient.username} - {self.frequency}"

# 4. Dinleme Günlüğü (Log)
class ListeningLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Dinlenen Frekans", null=True)
    
    duration_listened = models.IntegerField(default=0, help_text="Saniye cinsinden dinlenen süre")
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.frequency} - {'Tamamlandı' if self.is_completed else 'Eksik'}"

# 5. Seans Notları (Yeni)
class SessionNote(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_notes', limit_choices_to={'is_psychologist': False})
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notes', limit_choices_to={'is_psychologist': True})
    date = models.DateField(default=timezone.now, verbose_name="Seans Tarihi")
    note = models.TextField(verbose_name="Seans Notu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.patient.username} - {self.date}"