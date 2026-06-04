from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import RegexValidator
from .models import User, ContactMessage, Prescription, SessionNote, MusicTrack
import re

# Anket soruları — (field_name, kısa_etiket, açıklama)
SURVEY_QUESTIONS = [
    ('sleep_quality',  'Uyku Kalitesi',         'Genel uyku kalitenizi nasıl değerlendirirsiniz?'),
    ('stress_level',   'Stres Seviyesi',          'Son günlerde hissettiğiniz stres düzeyiniz nedir?'),
    ('focus_level',    'Odak / Konsantrasyon',    'Günlük görevlerde konsantre olabilme yeteneğiniz?'),
    ('mood_score',     'Ruh Hali',                'Genel ruh halinizi nasıl tanımlarsınız?'),
    ('anxiety_level',  'Anksiyete / Kaygı',       'Ne sıklıkla kaygı veya endişe hissediyorsunuz?'),
    ('fatigue_level',  'Yorgunluk Seviyesi',       'Kendinizi ne kadar yorgun hissediyorsunuz?'),
]

# ───────────────────────────────────────────────────────────────
# Tailwind input class'ları (form'lar arası tekrar kullanım)
# ───────────────────────────────────────────────────────────────
DARK_INPUT_CLASS = (
    "w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl "
    "text-white placeholder-stone-500 focus:outline-none focus:border-violet-500 transition-colors"
)
LIGHT_INPUT_CLASS = (
    "w-full px-4 py-2 mt-2 border rounded-md focus:outline-none "
    "focus:ring-1 focus:ring-blue-600 bg-gray-50 border-gray-300 text-gray-700"
)


class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Ad",
        required=True,
        validators=[RegexValidator(r'^[^\d]*$', 'İsim rakam içeremez.')]
    )
    last_name = forms.CharField(
        label="Soyad",
        required=True,
        validators=[RegexValidator(r'^[^\d]*$', 'Soyad rakam içeremez.')]
    )
    username = forms.CharField(
        label="Kullanıcı Adı",
        required=True,
        validators=[RegexValidator(r'^\S+$', 'Kullanıcı adı boşluk içeremez.')]
    )
    email = forms.EmailField(label="E-posta", required=True)
    password = forms.CharField(label="Şifre", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Şifre (Tekrar)", widget=forms.PasswordInput)
    role = forms.ChoiceField(
        choices=[
            ('patient', 'Danışan (Bir psikolog ile çalışacağım)'),
            ('individual', 'Bireysel Kullanıcı (Kendim kullanacağım)'),
            ('psychologist', 'Psikolog')
        ],
        widget=forms.RadioSelect,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        # Tüm alanlara Tailwind stilleri
        for field_name, field in self.fields.items():
            # Radyo butonları hariç diğerlerine standart input stili
            if field_name != 'role':
                field.widget.attrs['class'] = (
                    "w-full px-4 py-2 mt-2 border rounded-md focus:outline-none "
                    "focus:ring-1 focus:ring-blue-600 bg-gray-50 border-gray-300 text-gray-700"
                )
            # Eğer hata varsa kenarlığı kırmızı yapalım
            if self.errors.get(field_name):
                field.widget.attrs['class'] += " border-red-500"

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kullanımda.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı daha önce alınmış.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            return password
        # Basic validation - Django's AUTH_PASSWORD_VALIDATORS will handle the rest
        if len(password) < 8:
            raise forms.ValidationError("Şifre en az 8 karakter olmalıdır.")
        if not re.search(r'\d', password):
            raise forms.ValidationError("Şifre en az bir rakam içermelidir.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Şifre en az bir büyük harf içermelidir.")
        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Şifreler eşleşmiyor.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        role = self.cleaned_data.get('role')

        # Varsayılanlar — tüm yeni kullanıcılar e-posta doğrulamasını
        # tamamlayana kadar inaktiftir.
        user.is_psychologist = False
        user.is_individual = False
        user.is_active = False

        if role == 'psychologist':
            user.is_psychologist = True
            # Psikolog: e-posta doğrulamasından SONRA da admin onayını bekler
            # (login_view ve verify_email_view bu durumu yönetir).
        elif role == 'individual':
            user.is_individual = True

        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    # Bu form, is_active=False olan kullanıcıların girişini otomatik engeller
    error_messages = {
        'invalid_login': "Girdiğiniz kullanıcı adı veya şifre hatalı.",
        'inactive': "Hesabınız henüz onaylanmamış. Lütfen yönetici onayı bekleyin.",
    }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                "w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl "
                "text-white placeholder-stone-500 focus:outline-none focus:border-violet-500 transition-colors"
            )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check uniqueness, but allow current user to keep their email
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kullanımda.")
        return email


class ContactForm(forms.ModelForm):
    """Form for contact messages."""

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Adınız ve Soyadınız',
                'class': 'w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl text-white placeholder-stone-500 focus:outline-none focus:border-violet-500',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'E-posta adresiniz',
                'class': 'w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl text-white placeholder-stone-500 focus:outline-none focus:border-violet-500',
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Mesajınız...',
                'rows': 6,
                'class': 'w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl text-white placeholder-stone-500 focus:outline-none focus:border-violet-500 resize-none',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Ad ve soyad zorunludur.")
        if len(name) < 2:
            raise forms.ValidationError("Ad ve soyad en az 2 karakter olmalıdır.")
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError("Mesaj zorunludur.")
        if len(message) < 10:
            raise forms.ValidationError("Mesaj en az 10 karakter olmalıdır.")
        return message


class PrescriptionForm(forms.ModelForm):
    """Psikoloğun hastasına reçete oluşturma/düzenleme formu."""

    class Meta:
        model = Prescription
        fields = ['patient', 'frequency', 'duration_minutes', 'total_days', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 500,
                'placeholder': 'İsteğe bağlı not...',
                'style': 'resize: none; height: 7rem;',
            }),
        }
        labels = {
            'patient': 'Danışan',
            'frequency': 'Frekans',
            'duration_minutes': 'Günlük Süre (dakika)',
            'total_days': 'Toplam Gün',
            'notes': 'Notlar',
        }

    def __init__(self, *args, psychologist=None, **kwargs):
        super().__init__(*args, **kwargs)
        if psychologist is not None:
            self.fields['patient'].queryset = User.objects.filter(
                assigned_psychologist=psychologist,
                is_psychologist=False,
                is_individual=False,
                is_superuser=False,
            )
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + DARK_INPUT_CLASS).strip()

    def clean_duration_minutes(self):
        value = self.cleaned_data.get('duration_minutes')
        if value is None or value < 1:
            raise forms.ValidationError("Süre en az 1 dakika olmalıdır.")
        if value > 120:
            raise forms.ValidationError("Süre 120 dakikayı aşamaz.")
        return value

    def clean_total_days(self):
        value = self.cleaned_data.get('total_days')
        if value is None or value < 1:
            raise forms.ValidationError("Toplam gün sayısı en az 1 olmalıdır.")
        if value > 365:
            raise forms.ValidationError("Toplam gün sayısı 365'i aşamaz.")
        return value


class SessionNoteForm(forms.ModelForm):
    """Psikoloğun hastasına seans notu eklemek için form."""

    class Meta:
        model = SessionNote
        fields = ['date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Seans notu...'}),
        }
        labels = {
            'date': 'Seans Tarihi',
            'note': 'Not İçeriği',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + DARK_INPUT_CLASS).strip()

    def clean_note(self):
        note = self.cleaned_data.get('note', '').strip()
        if not note:
            raise forms.ValidationError("Seans notu boş olamaz.")
        if len(note) < 5:
            raise forms.ValidationError("Seans notu en az 5 karakter olmalıdır.")
        return note


class MusicTrackForm(forms.ModelForm):
    """Süper admin'in müzik kütüphanesine track ekleme/düzenleme formu."""

    class Meta:
        model = MusicTrack
        fields = ['title', 'description', 'icon', 'color', 'audio_file', 'is_active', 'order']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Kısa açıklama (opsiyonel)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ('is_active',):
                field.widget.attrs.setdefault('class', 'h-5 w-5 accent-violet-500')
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + LIGHT_INPUT_CLASS).strip()

    def clean_audio_file(self):
        audio = self.cleaned_data.get('audio_file')
        if audio and hasattr(audio, 'content_type'):
            if not audio.content_type.startswith('audio/'):
                raise forms.ValidationError("Yalnızca ses dosyası yüklenebilir.")
            max_size = 1024 * 1024 * 1024  # 1 GB
            if audio.size > max_size:
                raise forms.ValidationError("Ses dosyası 1 GB'tan büyük olamaz.")
        return audio


# ───────────────────────────────────────────────────────────────
# Kişisel Değerlendirme Anketi (ML Frekans Önerisi)
# ───────────────────────────────────────────────────────────────
class SurveyForm(forms.Form):
    sleep_quality  = forms.IntegerField(label='Uyku Kalitesi',        min_value=1, max_value=10)
    stress_level   = forms.IntegerField(label='Stres Seviyesi',        min_value=1, max_value=10)
    focus_level    = forms.IntegerField(label='Odak / Konsantrasyon',  min_value=1, max_value=10)
    mood_score     = forms.IntegerField(label='Ruh Hali',              min_value=1, max_value=10)
    anxiety_level  = forms.IntegerField(label='Anksiyete / Kaygı',     min_value=1, max_value=10)
    fatigue_level  = forms.IntegerField(label='Yorgunluk Seviyesi',    min_value=1, max_value=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].widget = forms.NumberInput(attrs={
                'type': 'range',
                'min': '1',
                'max': '10',
                'step': '1',
                'class': 'w-full h-2 bg-stone-700 rounded-lg appearance-none cursor-pointer accent-violet-500',
                'oninput': f"document.getElementById('val_{name}').textContent=this.value",
                'value': '5',
            })
            self.fields[name].initial = 5
