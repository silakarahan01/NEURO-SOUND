# NEURO SOUND

> Psikologların danışanlarına nöro-frekans (binaural beats) terapisi atayabildiği, danışanların tarayıcı üzerinde gerçek-zamanlı ses üreterek seanslarını takip ettiği bir Django web platformu.

[![CI](https://github.com/silakarahan01/Neuro-Sound/actions/workflows/ci.yml/badge.svg)](https://github.com/silakarahan01/Neuro-Sound/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-4.2_LTS-darkgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## İçindekiler
- [Proje Hakkında](#proje-hakkında)
- [Temel Özellikler](#temel-özellikler)
- [ML Frekans Öneri Modülü](#ml-frekans-öneri-modülü)
- [Mimari](#mimari)
- [Teknoloji Stack'i](#teknoloji-stacki)
- [Hızlı Kurulum (Yerel)](#hızlı-kurulum-yerel)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [Çevre Değişkenleri](#çevre-değişkenleri)
- [Test ve Kod Kalitesi](#test-ve-kod-kalitesi)
- [Kullanım Senaryoları](#kullanım-senaryoları)
- [Dokümantasyon](#dokümantasyon)
- [Akademik Bilgi](#akademik-bilgi)

---

## Proje Hakkında

NEURO SOUND, ses frekanslarının (Delta · Theta · Alpha · Beta · Gamma) beyin dalgaları üzerindeki etkisinden yararlanan tamamlayıcı bir terapi platformudur. Psikologlar danışanlarına frekans, süre ve gün bazında reçete oluşturur; danışanlar kendi panelinden Web Audio API ile **client-side** olarak üretilen sesleri dinler. Sistem her oturumun süresini ve tamamlanma durumunu otomatik kaydeder.

## Temel Özellikler

### Kullanıcı Rolleri
- **Süper Yönetici** — kullanıcıları, psikolog onaylarını, müzik kütüphanesini ve iletişim mesajlarını yönetir.
- **Psikolog** — danışan görür, reçete oluşturur/düzenler/siler, seans notu yazar, dinleme istatistiklerini izler.
- **Danışan (Hasta)** — atanan reçeteyi başlatır, geçmişini görür, müzik kütüphanesinden arkaplan sesi seçer.
- **Bireysel Kullanıcı** — psikolog atamasız bağımsız kullanım modu (serbest çalışma).

### Öne Çıkan Özellikler
- **Gerçek-zamanlı binaural beat üretimi** (tarayıcıda Web Audio API ile)
- **Reçete CRUD** (frekans + günlük süre + toplam gün + notlar)
- **E-posta doğrulama akışı** (kayıt sonrası 6 haneli kod, 15 dk geçerli)
- **Bildirim sistemi** (yeni reçete / yeni seans notu otomatik bildirim, navbar dropdown)
- **Abonelik middleware'i** (oturum cache'li, hızlı erişim kontrolü)
- **Dinamik müzik kütüphanesi** (admin panelinden yüklenebilir)
- **Modern arayüz** — Tailwind CSS, glassmorphism, dark theme
- **Erişilebilirlik** — `sr-only` ana içerik linki, ARIA etiketleri

## ML Frekans Öneri Modülü

**Bireysel kullanıcılar** psikolog olmaksızın sistemi kullandıklarında, 6 metriklik bir anket doldurarak kişiselleştirilmiş bir dinleme planı alır. Plan üç parametreyi içerir: hangi frekansın dinleneceği, günlük kaç dakika ve kaç günlük program uygulanacağı.

### Konum

```
main/
└── ml/
    ├── __init__.py
    ├── recommender.py       ← ana API: recommend() fonksiyonu
    ├── training_data.py     ← sentetik eğitim verisi üreteci + kural seti
    └── models/
        └── frequency_model.pkl   ← eğitilmiş model (git ignore edilmez)
```

### Girdi — Anket Metrikleri (1–10 arası)

| Alan | Açıklama | Düşük = ? | Yüksek = ? |
|------|----------|-----------|------------|
| `sleep_quality` | Uyku kalitesi | Kötü uyku | İyi uyku |
| `stress_level` | Stres seviyesi | Düşük stres | Yüksek stres |
| `focus_level` | Odak / konsantrasyon | Odak sorunu | Güçlü odak |
| `mood_score` | Ruh hali | Kötü ruh hali | İyi ruh hali |
| `anxiety_level` | Anksiyete | Düşük kaygı | Yüksek kaygı |
| `fatigue_level` | Yorgunluk | Enerjik | Yorgun |

### Çıktı

```python
from main.ml.recommender import recommend

result = recommend(
    sleep_quality=2, stress_level=5, focus_level=5,
    mood_score=5, anxiety_level=5, fatigue_level=7,
)
# {
#   'frequency':  'delta',   # delta | theta | alpha | beta | gamma
#   'minutes':    39,         # günlük önerilen dinleme süresi
#   'days':       21,         # program süresi
#   'confidence': 0.95,       # modelin güven skoru (0–1)
# }
```

### Frekans Seçim Mantığı

| Frekans | Öncelikli Gösterge | Günlük Süre | Program |
|---------|-------------------|-------------|---------|
| **Delta** (0.5–4 Hz) | Düşük uyku kalitesi (`≤3`) veya şiddetli yorgunluk (`≥8`) | 20–45 dk | 15–21 gün |
| **Theta** (4–8 Hz) | Yüksek anksiyete (`≥7`) veya yüksek stres (`≥7`) | 20–35 dk | 14–21 gün |
| **Alpha** (8–12 Hz) | Düşük ruh hali veya orta stres+anksiyete birlikte | 15–30 dk | 14–18 gün |
| **Beta** (12–30 Hz) | Düşük odak (`≤4`) veya belirgin yorgunluk | 15–25 dk | 10–15 gün |
| **Gamma** (30–100 Hz) | Genel iyilik — bakım/geliştirme amaçlı | 10–20 dk | 10–14 gün |

### Program Süresi Hesabı

Şiddet skoru; ilgili metriklerden ağırlıklı ortalama ile hesaplanır (0–1 arası):

| Şiddet | Gün Sayısı |
|--------|-----------|
| ≥ 0.70 (yüksek) | 21 gün |
| ≥ 0.50 (orta-yüksek) | 18 gün |
| ≥ 0.30 (orta) | 15 gün |
| < 0.30 (düşük) | 10 gün |

Günlük dakika da aynı şiddet skoru ile klinik aralık içinde interpole edilir (örn. delta için 20–45 dk arasında lineer).

### Model Teknik Detaylar

- **Algoritma:** `RandomForestClassifier` (scikit-learn)
  - 300 ağaç, `class_weight='balanced'`
- **Eğitim verisi:** 15 000 sentetik örnek; 6 özellik × tamsayı 1–10
- **Gürültü:** %2 etiket gürültüsü (overfitting önlemi)
- **Doğrulama:** 5-katlı stratified cross-validation
- **CV doğruluğu:** **%98.35 ± 0.13** (hedef: ≥ %90)

### Modeli Yeniden Eğitme

```bash
# Varsayılan: 15 000 örnek
python manage.py train_ml_model

# Farklı örnek sayısıyla
python manage.py train_ml_model --samples 20000
```

Eğitim sonunda CV doğruluğu terminale yazdırılır. %90 altında ise uyarı verilir. Model `main/ml/models/frequency_model.pkl` konumuna kaydedilir ve belleğe cache'lenir.

---

## Mimari

```
┌───────────────────────────────────────────────────────────┐
│                     Tarayıcı (Tailwind + JS)              │
│  binaural osc │ AJAX (save_progress) │ Bildirim dropdown  │
└──────────────────────────────┬────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼────────────────────────────┐
│                  gunicorn (3 worker, port 8000)           │
│              ┌────────────────────────────────┐           │
│              │  WhiteNoise (static files)     │           │
│              │  Django 4.2 LTS                │           │
│              │  ↳ SubscriptionMiddleware      │           │
│              │  ↳ context_processors          │           │
│              │     • notifications            │           │
│              └────────────────────────────────┘           │
└──────────────────────────────┬────────────────────────────┘
                               │
                          ┌────▼─────┐
                          │ MySQL 8  │  utf8mb4
                          └──────────┘
```

Detay için [`docs/architecture.md`](docs/architecture.md).

## Teknoloji Stack'i

| Katman      | Teknoloji                                              |
|-------------|--------------------------------------------------------|
| Backend     | Python 3.12, Django 4.2 LTS                            |
| Veritabanı  | MySQL 8 (utf8mb4)                                      |
| Frontend    | Tailwind CSS (CDN), Font Awesome 6, Web Audio API      |
| WSGI        | gunicorn + WhiteNoise (manifest static)                |
| Test        | pytest, pytest-django, pytest-cov, factory-boy         |
| Lint        | flake8, black, isort                                   |
| Container   | Dockerfile (multi-stage), docker-compose               |
| CI          | GitHub Actions (ubuntu-latest, MySQL service)          |

---

## Hızlı Kurulum (Yerel)

```bash
# 1. Klonla
git clone https://github.com/silakarahan01/Neuro-Sound.git
cd Neuro-Sound

# 2. Sanal ortam
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Bağımlılıklar
pip install -r requirements.txt
pip install -r requirements-dev.txt   # opsiyonel: test + lint

# 4. .env oluştur (placeholder'lı şablonu kopyala ve doldur)
cp .env.example .env
# SECRET_KEY ve DB_* değerlerini kendi ortamınıza göre düzenleyin

# 5. Veritabanı (MySQL'in çalışıyor olduğunu varsayıyoruz)
mysql -uroot -e "CREATE DATABASE neuro_db CHARACTER SET utf8mb4;"
python manage.py migrate
python manage.py createsuperuser

# 6. Geliştirme sunucusu
python manage.py runserver
```

Tarayıcı: <http://127.0.0.1:8000/>

## Docker ile Çalıştırma

Sıfırdan kurulum (web + MySQL):

```bash
cp .env.example .env
docker compose up --build
```

Yararlı komutlar:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose logs -f web
docker compose down                       # durdur
docker compose down -v                    # volume'ları da sil
```

`Dockerfile` multi-stage build kullanır (builder → runtime). Container içinde
`migrate → collectstatic → gunicorn` sırasıyla çalışır.

## Çevre Değişkenleri

Tam liste için [`.env.example`](.env.example).

| Değişken                          | Örnek                              | Notlar                       |
|-----------------------------------|------------------------------------|------------------------------|
| `SECRET_KEY`                      | _50 karakterlik rastgele_          | Üret: `manage.py shell -c "from django.core.management.utils import get_random_secret_key as g; print(g())"` |
| `DEBUG`                           | `False` (prod) / `True` (dev)      |                              |
| `ALLOWED_HOSTS`                   | `neurosound.com,www.neurosound.com`| Csv                          |
| `CSRF_TRUSTED_ORIGINS`            | `https://neurosound.com`           | Csv                          |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` |                  | MySQL 8 önerilir             |
| `EMAIL_BACKEND`                   | `django.core.mail.backends.smtp.EmailBackend` | Dev için `console.EmailBackend` |
| `SESSION_COOKIE_AGE`              | `1209600` (14 gün)                 |                              |

## Test ve Kod Kalitesi

```bash
# pytest (yeni testler) + Django TestCase'ler birlikte çalışır
pytest --cov=main --cov-report=term-missing

# Sadece yeni Faz 2 testleri
pytest main/test_phase2.py -v

# Lint
flake8 main neuro_core
black --check main neuro_core
isort --check-only main neuro_core

# Pre-commit hooks (kurulum: pre-commit install)
pre-commit run --all-files
```

`pyproject.toml` içinde black, isort, pytest ve coverage konfigürasyonu mevcut.

## Kullanım Senaryoları

### Süper Yönetici akışı
1. `/login/` ile gir → `/super-admin/` paneline yönlendirilir.
2. **Onaylar** sekmesinde yeni psikolog kayıtları görünür → "Kod Gönder" → "Onayla".
3. **Müzikler** sekmesinden ambient track yükle (mp3, ≤25 MB).
4. **Formlar** sekmesinden iletişim formu mesajlarını oku.

### Psikolog akışı
1. Kayıt ol → e-posta doğrula → admin onayını bekle.
2. Onaylandıktan sonra dashboard'da atanmış danışanları gör.
3. Danışana **çoklu frekans** reçetesi oluştur (AJAX ile her frekans ayrı kayıt).
4. Reçete listesinden **Düzenle** veya **Sil**.
5. Danışan detayında **Seans Notu** ekle → otomatik olarak hastaya bildirim.

### Danışan akışı
1. Kayıt ol (rol: Danışan veya Bireysel) → e-posta kodu gir → aktif.
2. Aboneliği yenile (`/subscription/payment/`, simülasyon).
3. Dashboard'dan reçeteyi seç → arkaplan müziği seç → **Başlat**.
4. Timer dolduğunda oturum otomatik tamamlanır, log kaydedilir.
5. Navbar bildirim ikonundan psikolog güncellemelerini gör.

## Dokümantasyon

| Doküman                                  | İçerik                                            |
|------------------------------------------|---------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md) | Request flow, middleware zinciri, DB ilişkileri |
| [`docs/api.md`](docs/api.md)             | AJAX endpoint'leri (save_progress, notifications) |
| [`docs/deployment.md`](docs/deployment.md) | Docker, env vars, MySQL, gunicorn detayları       |

## Akademik Bilgi

Bu proje bir lisans bitirme projesidir.

- **Geliştirici:** Sila Karahan
- **Repo:** <https://github.com/silakarahan01/Neuro-Sound>

---

## Lisans

MIT
