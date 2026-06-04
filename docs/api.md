# API Endpoint'leri

NEURO SOUND'un AJAX/JSON endpoint'leri. Tüm endpoint'ler login gerektirir
(`@login_required`) ve POST yöntemini kullanır (`@require_POST`). CSRF
koruması Django default'unun standartlarındadır — `X-CSRFToken` header'ı
zorunludur.

## `/api/save_progress/`

Dinleme oturumunun ilerlemesini kaydeder. Patient dashboard'daki timer
her tick'inde veya oturum sonunda çağrılır.

**Method:** `POST`
**Content-Type:** `application/json`

**Body:**
```json
{
  "duration": 120,
  "completed": false,
  "prescription_id": 42
}
```

| Alan              | Tip      | Zorunlu | Açıklama                               |
|-------------------|----------|---------|----------------------------------------|
| `duration`        | int (s)  | Evet    | Bugüne kadar dinlenen toplam saniye    |
| `completed`       | bool     | Hayır   | Oturum tamamlandı işareti              |
| `prescription_id` | int      | Hayır   | Eşlenen reçete (yoksa en yenisi alınır) |

**Yan etki:** `ListeningLog(user, today)` get_or_create + güncelleme;
`completed=true` ise `is_completed = True`.

**Response:**
```json
{ "status": "success" }
```

Hatalar: 400 (geçersiz JSON / int), 403 (CSRF), 405 (POST değilse).

---

## `/api/notifications/<int:id>/read/`

Tek bir bildirimi okundu işaretler. Bildirim dropdown'ı açıldığında
arka planda her unread bildirim için fire edilir.

**Method:** `POST` · **Body:** boş

**Yetki:** Yalnızca `notification.user == request.user` ise update gerçekleşir;
başka kullanıcının bildirimi update edilmez (filter ile garantilenir).

**Response:**
```json
{ "status": "success", "updated": 1 }
```

`updated` 0 ise: bildirim zaten okundu, ya da kullanıcının değil.

---

## `/api/notifications/read-all/`

Kullanıcının tüm okunmamış bildirimlerini tek seferde okundu yapar.

**Method:** `POST` · **Body:** boş

**Response:**
```json
{ "status": "success", "updated": 7 }
```

---

## CSRF Token alımı

Frontend tarafında token Django template'inden alınır:

```html
<form method="POST">{% csrf_token %}</form>
```

veya inline JS string olarak:
```js
const csrfToken = '{{ csrf_token }}';
fetch('/api/notifications/123/read/', {
  method: 'POST',
  headers: { 'X-CSRFToken': csrfToken },
});
```

base.html zaten her authenticated kullanıcı için CSRF token'ı
JavaScript scope'una enjekte eder (bildirim dropdown'ı için).

---

## Rate Limiting

`django-ratelimit` kullanılır:

| Endpoint                         | Limit       |
|----------------------------------|-------------|
| `/login/` (POST)                 | 5/m IP      |
| `/register/` (POST)              | 10/m IP    |
| `/verify-email/` (POST)          | 10/m IP    |
| `/verify-email/resend/` (POST)   | 3/m IP      |
| `/super-admin/send-code/<id>/`   | 10/m IP    |
| `/super-admin/approve/`          | 10/m IP    |

Limit aşıldığında HTTP 403 döner.
