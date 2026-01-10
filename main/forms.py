from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import RegexValidator
from .models import User
import re

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
            # Eğer hata varsa kenarlığı kırmızı yapalım (isteğe bağlı gelişmiş ayar)
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
        if not password: return password
        if len(password) < 8: raise forms.ValidationError("Şifre en az 8 karakter olmalıdır.")
        if not re.search(r'\d', password): raise forms.ValidationError("Şifre en az bir rakam içermelidir.")
        if not re.search(r'[A-Z]', password): raise forms.ValidationError("Şifre en az bir büyük harf içermelidir.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        role = self.cleaned_data.get('role')
        
        # Varsayılanlar
        user.is_psychologist = False
        user.is_individual = False
        user.is_active = True # Danışanlar ve Bireysel aktif başlar
        
        if role == 'psychologist':
            user.is_psychologist = True
            user.is_active = False # Onay bekler
        elif role == 'individual':
            user.is_individual = True
            # Bireysel de aktiftir
            
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
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                "w-full px-4 py-3 bg-stone-800/50 border border-stone-700 rounded-xl "
                "text-white placeholder-stone-500 focus:outline-none focus:border-violet-500 transition-colors"
            )