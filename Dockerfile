# NEURO SOUND — Multi-stage Dockerfile (Python 3.12 slim)
# Build:    docker build -t neurosound:latest .
# Run:      docker compose up

# ─── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# mysqlclient için gereken sistem kütüphaneleri (build-time)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ─── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=neuro_core.settings

# Yalnızca runtime için gerekli MySQL client kütüphaneleri
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmariadb3 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1000 neuro

WORKDIR /app

# Wheels'ı builder stage'inden kopyala ve kur
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && pip install --no-cache-dir gunicorn>=21.2 whitenoise>=6.6 \
    && rm -rf /wheels

# Uygulama kaynak kodu
COPY --chown=neuro:neuro . .

# Statik dosyaları topla (whitenoise için)
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R neuro:neuro /app/staticfiles /app/media /app/logs

USER neuro

EXPOSE 8000

# Healthcheck (basit)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/login/ || exit 1

# entrypoint: migrate + collectstatic + gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn neuro_core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
