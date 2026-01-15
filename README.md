# NEURO SOUND

**Neuro Sound**, psikologların danışanlarına nöro-frekans (binaural beats) terapisi atayabildiği ve süreçlerini takip edebildiği web tabanlı bir platformdur.

## 🚀 Proje Hakkında

Bu proje, ses frekanslarının (Delta, Theta, Alpha, Beta, Gamma) beyin dalgaları üzerindeki etkisini kullanarak tamamlayıcı bir terapi yöntemi sunar. Psikologlar, danışanlarına özel reçeteler (frekans, süre, gün) oluşturabilir ve danışanlar kendi panellerinden bu sesleri dinleyerek tedavilerini uygularlar. Sistem, dinleme sürelerini ve oturum tamamlanma durumlarını otomatik olarak kaydeder.

## ✨ Temel Özellikler

### 👥 Kullanıcı Rolleri
*   **Danışan (Hasta):** Kendisine atanan reçeteleri görüntüler, terapiyi başlatır ve dinleme geçmişini takip eder.
*   **Psikolog:** Danışan ekler, reçete oluşturur, danışanların ilerlemesini grafik ve tablolarla izler, özel seans notları alır.
*   **Yönetici (Admin):** Sistem genelindeki kullanıcıları ve ayarları yönetir.

### 🎧 Özellikler
*   **Dinamik Binaural Beat Üretimi:** Web Audio API kullanılarak tarayıcı üzerinde gerçek zamanlı ses frekansı üretimi.
*   **Reçete Sistemi:** Frekans türü, günlük süre ve toplam gün sayısı belirleme.
*   **Takip ve Raporlama:** Günlük dinleme süreleri, tamamlanan seanslar ve kaçırılan günlerin takibi.
*   **Güvenli Not Sistemi:** Psikologların her seans için ayrı ayrı tarihli notlar tutabildiği özel modül.
*   **Modern Arayüz:** Tailwind CSS ile tasarlanmış, karanlık mod (dark mode) ve cam efektli (glassmorphism) kullanıcı dostu arayüz.

## 🛠 Teknolojiler

*   **Backend:** Python, Django
*   **Frontend:** HTML5, CSS3 (Tailwind CSS), JavaScript
*   **Veritabanı:** SQLite (Geliştirme) / MySQL (Prodüksiyon uyumlu)
*   **Ses Motoru:** Web Audio API (Client-side)

## ⚙️ Kurulum

Projeyi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyin:

1.  **Repoyu Klonlayın:**
    ```bash
    git clone https://github.com/kullaniciadi/neuro-sound.git
    cd neuro-sound
    ```

2.  **Sanal Ortam (Virtual Environment) Oluşturun ve Aktifleştirin:**
    ```bash
    python -m venv venv
    # Windows için:
    venv\Scripts\activate
    # Mac/Linux için:
    source venv/bin/activate
    ```

3.  **Gerekli Paketleri Yükleyin:**
    ```bash
    pip install django
    # Eğer requirements.txt varsa:
    # pip install -r requirements.txt
    ```

4.  **Veritabanı Migrasyonlarını Uygulayın:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Süper Kullanıcı (Admin) Oluşturun:**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Sunucuyu Başlatın:**
    ```bash
    python manage.py runserver
    ```

Tarayıcınızda `http://127.0.0.1:8000/` adresine giderek projeyi görüntüleyebilirsiniz.

## 📝 Kullanım

1.  **Psikolog Girişi:** Psikolog hesabıyla giriş yapın. "Danışan Ekle" butonunu kullanarak sisteme yeni bir danışan kaydedin.
2.  **Reçete Atama:** Eklediğiniz danışanın detay sayfasına gidin ve ona uygun bir frekans reçetesi (örn: Alpha, 15 dakika, 10 gün) tanımlayın.
3.  **Danışan Girişi:** Oluşturulan danışan bilgileriyle giriş yapın. Dashboard'da atanan reçeteyi göreceksiniz. "Oynat" butonuna basarak seansı başlatın.
4.  **Takip:** Psikolog panelinden danışanın dinleme loglarını ve ilerlemesini kontrol edin.

## 🤝 Katkıda Bulunma

1.  Forklayın.
2.  Feature branch oluşturun (`git checkout -b feature/YeniOzellik`).
3.  Değişikliklerinizi commit yapın (`git commit -m 'Yeni özellik eklendi'`).
4.  Branch'inizi pushlayın (`git push origin feature/YeniOzellik`).
5.  Pull Request oluşturun.

