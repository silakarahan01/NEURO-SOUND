# Mimari

## Yüksek Seviye Akış

```
Browser ──► gunicorn ──► WhiteNoise (static) ──► Django (4.2)
                                                    │
                                                    ├── SecurityMiddleware
                                                    ├── SessionMiddleware
                                                    ├── CsrfViewMiddleware
                                                    ├── AuthenticationMiddleware
                                                    ├── MessagesMiddleware
                                                    ├── XFrameOptionsMiddleware
                                                    └── SubscriptionMiddleware  ◄── (özel)
                                                    │
                                                    ▼
                                                 main.urls ──► views ──► ORM ──► MySQL 8
```

## URL → View Eşlemesi (özet)

| URL kalıbı                                          | View                              | Erişim       |
|-----------------------------------------------------|-----------------------------------|--------------|
| `/`                                                 | `landing_view`                    | Genel        |
| `/login/`, `/register/`, `/logout/`                 | `auth.*`                          | Genel        |
| `/verify-email/`, `/verify-email/resend/`           | `verify_email_view`               | Session-bound|
| `/profile/`                                         | `profile_view`                    | Login req.   |
| `/patient/`                                         | `patient_dashboard`               | Login + sub  |
| `/library/`                                         | `music_library`                   | Login        |
| `/psychologist/`                                    | `psychologist_dashboard`          | is_psychologist |
| `/psychologist/prescription/<id>/edit/`             | `prescription_update_view`       | Reçete sahibi   |
| `/psychologist/delete-prescription/<id>/`           | `delete_prescription`             | Reçete sahibi   |
| `/super-admin/...`                                  | `admin.*`                         | is_superuser |
| `/subscription/payment/`                            | `payment_view`                    | Login        |
| `/api/save_progress/`                               | `save_progress`                   | AJAX, login  |
| `/api/notifications/<id>/read/`                     | `mark_notification_read`          | AJAX, login  |
| `/api/notifications/read-all/`                      | `mark_all_notifications_read`     | AJAX, login  |
| `/ns-yonetim/`                                      | Django admin (gizli URL)          | is_staff     |

## Veri Modeli

### Çekirdek varlıklar

```
       ┌──────────────┐  assigned_psychologist (self FK)
       │     User     │◄─────────┐
       │  (custom)    │          │
       └──────┬───────┘          │
              │                  │
   ┌──────────┼──────────────────┘
   │          │
   ▼          ▼
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Prescription│    │ ListeningLog    │    │ SessionNote  │
│ patient     │    │ user, date(*)   │    │ patient      │
│ assigned_by │    │ frequency       │    │ created_by   │
│ frequency   │    │ duration_listen │    │ note         │
│ duration_min│    │ is_completed    │    │ date         │
│ total_days  │    │                 │    │              │
└─────────────┘    └─────────────────┘    └──────────────┘
        (*) unique_together (user, date)

┌──────────────────┐    ┌─────────────────────┐
│ SubscriptionPlan │◄───│ UserSubscription    │
│ name (PSY/IND)   │    │ user, plan          │
│ price            │    │ start_date, end_date│
└──────────────────┘    │ is_active           │
                        └─────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌────────────┐
│ MusicTrack   │  │ ContactMsg   │  │Notification│
│ title, audio │  │ name, email  │  │user, msg   │
│ icon, color  │  │ message      │  │link_url    │
│ order, active│  │ is_read      │  │is_read     │
└──────────────┘  └──────────────┘  └────────────┘
```

### Önemli Tasarım Kararları
- `User.assigned_psychologist` self-FK, `on_delete=SET_NULL` → psikolog silindiğinde danışan silinmez.
- `Prescription.patient` `limit_choices_to` ile yalnızca gerçek danışanlara izin verir (psikolog/bireysel/superuser değil).
- `ListeningLog` `unique_together(user, date)` → günde tek log kaydı.
- `Notification` `(user, is_read, -created_at)` indeksi → unread sorgusu hızlı.
- `Prescription.full_clean` save'de çalışır → DB seviyesinde de tutarlılık.

## Middleware: SubscriptionMiddleware

`main.middleware.SubscriptionMiddleware` her authenticated isteği aboneliğe karşı kontrol eder.

- Session cache (`request.session['_sub_active']`) ile DB hit'i önler.
- EXEMPT_PREFIXES: `/admin/`, `/login/`, `/register/`, `/payment/`, `/static/`, `/media/` vb.
- Aktif aboneliği olmayan kullanıcılar `/subscription/payment/`'a yönlendirilir.
- Süperuser ve psikolog onay-bekleyen kullanıcılar middleware'den muaftır.

## Context Processor: notifications

`main.context_processors.notifications` her template render'ında çalışır:
- `unread_notifications_count` — okunmamış bildirim sayısı
- `recent_notifications` — son 5 bildirim (Notification queryset)

Anonim kullanıcılar için her ikisi de boş döner.

## Web Audio API (Client-side)

`patient_dashboard.html` içindeki JS:

```
AudioContext
  ├── OscillatorNode (sol kulak: baseFreq Hz)
  ├── OscillatorNode (sağ kulak: baseFreq + targetBeat Hz)
  └── GainNode → ChannelMerger → destination
```

Frekans farkı (`targetBeat`) seçilen frekans bandına göre belirlenir. Background ambient track varsa `<audio loop>` ile birlikte çalar. Timer dolunca `save_progress` AJAX'ı `completed=true` ile çağrılır, ListeningLog güncellenir.

## Loglama

`logs/django.log` (RotatingFileHandler, 5 MB × 3 backup).

| Logger    | Level   | Hedef          |
|-----------|---------|----------------|
| `django`  | WARNING | console + file |
| `main`    | INFO    | console + file |

`main` logger'ı view'larda `logger = logging.getLogger('main')` ile kullanılır (kayıt, reçete oluşturma, doğrulama kodu, abonelik yenileme vb. olaylar).
