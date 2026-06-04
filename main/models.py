from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .constants import FREQUENCIES, FREQUENCY_CHOICES


# 0. Özel Manager — Module-level (migration writer nested class'ları
# serialize edemiyor). DjangoUserManager'dan miras alır; böylece
# normalize_email / create_user / create_superuser metodları korunur.
class UserManager(DjangoUserManager):
    """Custom manager for User model."""

    def active_psychologists(self):
        """Aktif psikologları döndürür."""
        return self.filter(is_psychologist=True, is_active=True)


# 1. Özelleştirilmiş Kullanıcı Modeli
class User(AbstractUser):
    is_psychologist = models.BooleanField(default=False, verbose_name="Psikolog Mu?")
    is_individual = models.BooleanField(default=False, verbose_name="Bireysel Kullanıcı Mı?")

    # Psikolog onayı için gerekli alanlar
    verification_code = models.CharField(max_length=6, blank=True, null=True, verbose_name="Doğrulama Kodu")
    verification_code_expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Doğrulama Kodu Süresi Dolacak")

    # HASTA ATAMA SİSTEMİ
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

    # Kişisel Bilgiler
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefon Numarası")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Doğum Tarihi")

    objects = UserManager()

    def clean(self):
        """Bir kullanıcı hem psikolog hem bireysel olamaz."""
        super().clean()
        if self.is_psychologist and self.is_individual:
            raise ValidationError(
                "Bir kullanıcı hem 'Psikolog' hem 'Bireysel Kullanıcı' olamaz. Lütfen yalnızca birini seçin."
            )

    def save(self, *args, **kwargs):
        # Yeni kullanıcılar için clean() ile doğrulama yap
        if self.pk is None:
            self.full_clean()
        super().save(*args, **kwargs)

    def get_role_display(self):
        if self.is_superuser:
            return "Süper Yönetici"
        if self.is_psychologist:
            return "Psikolog"
        if self.is_individual:
            return "Bireysel Kullanıcı"
        return "Danışan"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# 3. Reçete Modeli
class Prescription(models.Model):
    # Bir hastanın geçmişe dönük birden fazla reçete kaydı olabilir
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        # Yalnızca gerçek danışanlar: psikolog değil, bireysel değil, süper admin değil
        limit_choices_to={'is_psychologist': False, 'is_individual': False, 'is_superuser': False}
    )

    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_prescriptions', limit_choices_to={'is_psychologist': True})
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    duration_minutes = models.IntegerField(default=15, help_text="Günlük dinleme süresi (dk)")
    total_days = models.IntegerField(default=15, help_text="Kaç gün sürecek?")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        """Validate prescription data."""
        super().clean()
        if self.total_days < 1:
            raise ValidationError("Toplam gün sayısı en az 1 olmalıdır.")
        if self.duration_minutes < 1:
            raise ValidationError("Dinleme süresi en az 1 dakika olmalıdır.")
        if self.assigned_by and not self.assigned_by.is_psychologist:
            raise ValidationError("Reçete yalnızca psikolog tarafından atanabilir.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
        unique_together = ('user', 'date', 'frequency')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.frequency} - {'Tamamlandı' if self.is_completed else 'Eksik'}"


# 5. Anket Yanıtı ve ML Öneri Sonucu
class SurveyResponse(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='survey_responses',
        limit_choices_to={'is_individual': True},
        verbose_name="Kullanıcı",
    )
    # Anket skorları (1–10)
    sleep_quality  = models.IntegerField(verbose_name="Uyku Kalitesi")
    stress_level   = models.IntegerField(verbose_name="Stres Seviyesi")
    focus_level    = models.IntegerField(verbose_name="Odak / Konsantrasyon")
    mood_score     = models.IntegerField(verbose_name="Ruh Hali")
    anxiety_level  = models.IntegerField(verbose_name="Anksiyete Seviyesi")
    fatigue_level  = models.IntegerField(verbose_name="Yorgunluk Seviyesi")

    # ML çıktısı
    recommended_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name="Önerilen Frekans",
    )
    recommended_minutes = models.IntegerField(verbose_name="Önerilen Günlük Süre (dk)")
    recommended_days = models.IntegerField(default=15, verbose_name="Önerilen Program Süresi (gün)")
    ml_confidence = models.FloatField(default=0.0, verbose_name="Model Güven Skoru")

    # Dinamik döngü (recommended_days'e göre)
    plan_start_date = models.DateField(verbose_name="Plan Başlangıç Tarihi")
    plan_expires_at = models.DateField(verbose_name="Plan Bitiş Tarihi")
    renewal_notified = models.BooleanField(default=False, verbose_name="Yenileme Bildirimi Gönderildi")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Anket Yanıtı"
        verbose_name_plural = "Anket Yanıtları"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    @property
    def is_expired(self):
        return timezone.now().date() > self.plan_expires_at

    @property
    def days_remaining(self):
        delta = (self.plan_expires_at - timezone.now().date()).days
        return max(0, delta)

    @property
    def days_completed(self):
        return max(0, self.recommended_days - self.days_remaining)

    def __str__(self):
        return (
            f"{self.user.username} — {self.recommended_frequency} "
            f"({self.plan_start_date})"
        )


# 6. Seans Notları
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


# 6. Abonelik Sistemi
class SubscriptionPlan(models.Model):
    PLAN_TYPES = (
        ('PSYCHOLOGIST', 'Psikolog Aboneliği'),
        ('INDIVIDUAL', 'Bireysel Abonelik'),
    )
    name = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True, verbose_name="Plan Adı")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fiyat (TL)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_name_display()} - {self.price} TL"

    class Meta:
        verbose_name = "Abonelik Planı"
        verbose_name_plural = "Abonelik Planları"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta")
    message = models.TextField(verbose_name="Mesaj")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu?")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class MusicTrack(models.Model):
    ICON_CHOICES = [
        ('fa-music',       'Müzik Notası'),
        ('fa-cloud-rain',  'Yağmur'),
        ('fa-tree',        'Orman'),
        ('fa-water',       'Su / Okyanus'),
        ('fa-om',          'Zen'),
        ('fa-spa',         'Spa'),
        ('fa-wind',        'Rüzgar'),
        ('fa-fire',        'Ateş'),
        ('fa-leaf',        'Yaprak'),
        ('fa-moon',        'Ay'),
        ('fa-sun',         'Güneş'),
        ('fa-snowflake',   'Kar'),
        ('fa-dove',        'Barış'),
        ('fa-guitar',      'Gitar'),
        ('fa-drum',        'Davul'),
    ]
    COLOR_CHOICES = [
        ('violet',  'Mor'),
        ('blue',    'Mavi'),
        ('emerald', 'Yeşil'),
        ('cyan',    'Camgöbeği'),
        ('amber',   'Turuncu'),
        ('rose',    'Pembe'),
        ('indigo',  'İndigo'),
        ('teal',    'Teal'),
        ('stone',   'Gri'),
    ]

    title       = models.CharField(max_length=100, verbose_name="Başlık")
    description = models.CharField(max_length=200, blank=True, verbose_name="Açıklama")
    icon        = models.CharField(max_length=50, choices=ICON_CHOICES, default='fa-music', verbose_name="İkon")
    color       = models.CharField(max_length=20, choices=COLOR_CHOICES, default='violet', verbose_name="Renk")
    audio_file  = models.FileField(upload_to='music/', verbose_name="Ses Dosyası")
    is_active   = models.BooleanField(default=True, verbose_name="Aktif")
    order       = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Müzik Parçası"
        verbose_name_plural = "Müzik Parçaları"

    def __str__(self):
        return self.title


class Notification(models.Model):
    """Kullanıcıya gösterilecek bildirim.

    create_notification(user, message, link_url) yardımcısı ile oluşturulur;
    örn. yeni reçete atandığında veya yeni seans notu eklendiğinde.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Alıcı",
    )
    message = models.CharField(max_length=255, verbose_name="Mesaj")
    link_url = models.CharField(max_length=255, blank=True, default='', verbose_name="Bağlantı")
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bildirim"
        verbose_name_plural = "Bildirimler"
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


class UserSubscriptionQuerySet(models.QuerySet):
    """Custom QuerySet for UserSubscription."""

    def active(self):
        """Get only active subscriptions."""
        today = timezone.now().date()
        return self.filter(is_active=True, end_date__gte=today)


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usersubscription_set', verbose_name="Kullanıcı")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, verbose_name="Seçilen Plan")
    start_date = models.DateField(default=timezone.now, verbose_name="Başlangıç Tarihi")
    end_date = models.DateField(verbose_name="Bitiş Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserSubscriptionQuerySet.as_manager()

    @property
    def is_expired(self):
        """Check if subscription has expired."""
        return timezone.now().date() > self.end_date

    def clean(self):
        """Validate subscription data."""
        super().clean()
        if self.start_date > self.end_date:
            raise ValidationError("Başlangıç tarihi bitiş tarihinden sonra olamaz.")

    def __str__(self):
        return f"{self.user.username} - {self.plan} ({self.end_date})"

    class Meta:
        verbose_name = "Kullanıcı Aboneliği"
        verbose_name_plural = "Kullanıcı Abonelikleri"
