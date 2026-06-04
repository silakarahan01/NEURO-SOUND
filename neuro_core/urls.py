from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Admin URL güvenlik için standart /admin/'den farklı bir yola taşındı.
admin.site.site_header = "NeuroSound Sistem Yönetimi"
admin.site.site_title = "NeuroSound Admin"
admin.site.index_title = "Yönetim Paneli"

urlpatterns = [
    path('ns-yonetim/', admin.site.urls),   # Django admin — gizli URL
    path('', include('main.urls')),          # Tüm uygulama URL'leri
]

# Özel hata sayfaları (templates/404.html, 500.html, 403.html otomatik render).
# DEBUG=True iken Django'nun teknik debug sayfası gösterilir; bu handler'lar
# yalnızca DEBUG=False'da etkindir.
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
handler403 = 'django.views.defaults.permission_denied'

# Geliştirme ortamında statik ve medya dosyaları
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
