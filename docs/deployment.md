# Deployment

## 1. Hızlı Yol — Docker Compose

Yerel veya küçük VPS için hazır kurulum:

```bash
git clone https://github.com/silakarahan01/Neuro-Sound.git
cd Neuro-Sound
cp .env.example .env

# .env dosyasında en azından şunları ayarla:
#   SECRET_KEY=...     (manage.py shell ile yeni üret)
#   DEBUG=False
#   ALLOWED_HOSTS=domain.com,www.domain.com
#   DB_PASSWORD=<güçlü-parola>

docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Erişim: `http://localhost:8000/`

`docker-compose.yml` iki servis tanımlar:
- **db** — MySQL 8, persistent volume (`db_data`), healthcheck.
- **web** — gunicorn 3 worker, port 8000, `media_data` ve `logs_data` volume'ları.

## 2. Manuel Production Kurulumu (Gunicorn + Nginx)

Sistem paketleri:

```bash
sudo apt-get install -y python3.12 python3.12-venv \
    default-libmysqlclient-dev pkg-config build-essential \
    mysql-server nginx
```

Uygulama kullanıcısı:

```bash
sudo useradd -m -s /bin/bash neuro
sudo -iu neuro
git clone https://github.com/silakarahan01/Neuro-Sound.git app
cd app
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # düzenle
python manage.py migrate
python manage.py collectstatic --noinput
```

Systemd unit (`/etc/systemd/system/neurosound.service`):

```ini
[Unit]
Description=NEURO SOUND gunicorn
After=network.target mysql.service

[Service]
User=neuro
WorkingDirectory=/home/neuro/app
EnvironmentFile=/home/neuro/app/.env
ExecStart=/home/neuro/app/venv/bin/gunicorn neuro_core.wsgi:application \
          --bind 127.0.0.1:8000 --workers 3 --access-logfile -
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now neurosound
```

Nginx (`/etc/nginx/sites-available/neurosound`):

```nginx
server {
    listen 80;
    server_name neurosound.com www.neurosound.com;

    location /static/ {
        alias /home/neuro/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    location /media/ {
        alias /home/neuro/app/media/;
        expires 7d;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 30M;   # MusicTrack 25MB üst sınırı için
    }
}
```

HTTPS için Let's Encrypt:

```bash
sudo certbot --nginx -d neurosound.com -d www.neurosound.com
```

## 3. Çevre Değişkenleri (Production)

`.env.example` baz alınarak en az şu değerler **mutlaka** ayarlanmalıdır:

| Değişken               | Önemi                                                        |
|------------------------|--------------------------------------------------------------|
| `SECRET_KEY`           | Asla repository'ye girmemeli; her ortamda farklı olmalı.     |
| `DEBUG=False`          | True bırakılırsa stack trace'ler ifşa olur.                  |
| `ALLOWED_HOSTS`        | Production domain'leri (Django Host header doğrulaması).     |
| `CSRF_TRUSTED_ORIGINS` | HTTPS scheme'li domain'ler (Django 4.x zorunlu).             |
| `DB_*`                 | MySQL 8 credentials (root değil, yetkili app user).          |
| `EMAIL_BACKEND`        | `smtp.EmailBackend` + `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` |

## 4. Static & Media

WhiteNoise sayesinde `/static/` reverse proxy gerektirmez:
- `STORAGES['staticfiles'] = whitenoise.storage.CompressedManifestStaticFilesStorage`
- `python manage.py collectstatic` → `staticfiles/` dizinine hash'li sürümleri üretir.

Media dosyaları (kullanıcı yüklediği müzik track'leri vb.) `media/` dizininde tutulur ve nginx tarafından servis edilir.

## 5. Veritabanı Yedekleme

Cron örneği (her gece 03:00):

```bash
0 3 * * * mysqldump -uneuro -p"$DB_PASSWORD" neuro_db | gzip > \
          /var/backups/neuro_db_$(date +\%Y\%m\%d).sql.gz
```

Restore:
```bash
gunzip -c neuro_db_20260426.sql.gz | mysql -uneuro -p neuro_db
```

## 6. CI/CD (GitHub Actions)

`.github/workflows/ci.yml` her push ve PR'da:

1. Python 3.12 + MySQL 8 service container kurar
2. Bağımlılıkları yükler
3. `flake8` + `black --check` (warning-only, bitirme için non-blocking)
4. `python manage.py check` + `migrate`
5. `pytest --cov=main`
6. Coverage raporu artifact olarak yüklenir

## 7. Log & Monitoring

- `logs/django.log` — RotatingFileHandler (5MB × 3)
- Production'da `journalctl -u neurosound -f` ile gunicorn akışını takip et
- Hata izleme için ileride **Sentry** entegrasyonu önerilir (`sentry-sdk[django]`)

## 8. Health Check

Container'da basit healthcheck:
```yaml
healthcheck:
  test: curl -f http://127.0.0.1:8000/login/ || exit 1
  interval: 30s
```

Production için ayrı bir `/healthz/` endpoint'i eklenebilir (DB ping kontrolü dahil).
