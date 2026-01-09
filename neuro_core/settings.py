import os
from pathlib import Path

# Projenin ana dizini (manage.py'nin olduğu yer)
BASE_DIR = Path(__file__).resolve().parent.parent

# Güvenlik anahtarı
SECRET_KEY = 'django-insecure-gizli-anahtar-buraya'

# Geliştirme modu
DEBUG = True

ALLOWED_HOSTS = []

# Yüklü Uygulamalar
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main', # Uygulamamız
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'neuro_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # ÖNEMLİ: HTML dosyalarını manage.py'nin yanındaki 'templates' klasöründe ara
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'neuro_core.wsgi.application'

# Veritabanı Ayarları
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'neuro_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# --- STATİK DOSYA AYARLARI ---
STATIC_URL = 'static/'

# Django'nun proje klasöründeki 'static' klasörünü bulmasını sağlayan ayar:
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Özel Kullanıcı Modeli
AUTH_USER_MODEL = 'main.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- E-POSTA AYARLARI (Gerçek Gmail SMTP) ---
# Burayı kendi bilgilerinizle doldurmanız gerekiyor:

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Lütfen aşağıdaki iki satırı kendi bilgilerinizle değiştirin:
EMAIL_HOST_USER = 'seninmailin@gmail.com'   # Gönderici olacak Gmail adresiniz
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx' # Gmail'den alacağınız 16 haneli "Uygulama Şifresi"

# --- MEDYA (Yüklenen Dosyalar / Müzikler) AYARLARI ---
# Müzik dosyalarının (MP3) erişilebilir olması için gereklidir.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Kullanıcı giriş yapmadan sayfaya girmeye çalışırsa 'login' sayfasına atılsın:
LOGIN_URL = 'login'