from pathlib import Path
from decouple import config, Csv

# ─── Proje Kök Dizini ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Güvenlik Anahtarı (Zorunlu: .env dosyasından okunur) ────────
SECRET_KEY = config('SECRET_KEY')

# ─── Geliştirme/Production Modu ──────────────────────────────────
DEBUG = config('DEBUG', default=False, cast=bool)

# ─── İzin Verilen Hostlar ────────────────────────────────────────
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ─── Yüklü Uygulamalar ───────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

# ─── Middleware ───────────────────────────────────────────────────
# WhiteNoise SecurityMiddleware'in hemen ardından gelir; production'da
# Django'nun static dosyalarını verir (gunicorn arkasında nginx olmadan).
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'neuro_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'neuro_core.wsgi.application'

# ─── Veritabanı (.env'den okunur) ────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='neuro_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ─── Şifre Doğrulama ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

# ─── Dil & Saat Dilimi ───────────────────────────────────────────
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# ─── Statik Dosyalar ─────────────────────────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: production'da statik dosyaları sıkıştırılmış ve manifest'li sunar.
# DEBUG=True'da Django dev server zaten static'leri verir; bu storage yine de
# collectstatic sonrası hash'li dosya isimleri üretir.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ─── Medya Dosyaları ─────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Özel Kullanıcı Modeli ───────────────────────────────────────
AUTH_USER_MODEL = 'main.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Authentication URLs ─────────────────────────────────────────
# NOT: login_view rol bazlı yönlendirmeyi kendisi yapar; aşağıdaki ayarlar
# yalnızca fallback amaçlıdır.
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'profile_view'
LOGOUT_REDIRECT_URL = 'landing'

# ─── Oturum Ayarları ─────────────────────────────────────────────
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=1209600, cast=int)  # 14 gün
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=False, cast=bool)
SESSION_SAVE_EVERY_REQUEST = True

# ─── E-posta Ayarları (.env'den okunur) ──────────────────────────
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='NEURO SOUND <info@neurosound.com>')

# ─── Dosya Yükleme Limitleri ─────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024   # 1 GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024   # 1 GB

# ─── Uygulama Değişkenleri ───────────────────────────────────────
ADMIN_CONTACT_EMAIL = config('ADMIN_CONTACT_EMAIL', default='info@neurosound.com')

# ─── Abonelik Fiyatlandırması ────────────────────────────────────
SUBSCRIPTION_PRICES = {
    'INDIVIDUAL': 50.00,
    'PSYCHOLOGIST': 500.00,
}

# ─── CSRF İçin Güvenilir Kaynaklar (.env'den okunur) ─────────────
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv(),
)

# ─── Production Güvenlik Ayarları (DEBUG=False iken aktif) ───────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000          # 1 yıl
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# ─── Loglama Yapılandırması ──────────────────────────────────────
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} — {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 5 * 1024 * 1024,   # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'main': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
