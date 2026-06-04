"""
Frekans öneri modeli için sentetik eğitim verisi üretir.

Kural tabanlı etiketleme (açık eşikler + deterministik fallback):
  Katı kurallar, RandomForest'in yüksek doğrulukla öğrenebileceği
  düzlemsel karar sınırları oluşturur.

  Öncelik sırası (ilk uyan kural kazanır):
  1. sleep ≤ 3                          → delta  (akut uyku yokunluğu)
  2. anxiety ≥ 7 OR stress ≥ 7          → theta  (akut stres/anksiyete)
  3. sleep ≤ 4 OR fatigue ≥ 8           → delta  (uyku + şiddetli yorgunluk)
  4. mood ≤ 3 OR (anxiety≥6 AND stress≥6)→ alpha  (akut ruh hali)
  5. focus ≤ 3                          → beta   (akut odak)
  6. (anxiety≥5 AND stress≥5) OR mood≤4 → alpha  (orta ruh hali)
  7. focus ≤ 4 OR fatigue ≥ 7           → beta   (orta odak/yorgunluk)
  8. tüm iyi metrikler                  → gamma  (optimal sağlık)
  fallback: numerik deficit skoru       → en büyük ihtiyaç
"""

import numpy as np

FREQUENCY_LABELS = ['alpha', 'beta', 'delta', 'gamma', 'theta']


def _label(sleep, stress, focus, mood, anxiety, fatigue):
    # Kural 1 — akut uyku yokunluğu
    if sleep <= 3:
        return 'delta'
    # Kural 2 — akut stres veya anksiyete
    if anxiety >= 7 or stress >= 7:
        return 'theta'
    # Kural 3 — ciddi uyku sorunu veya şiddetli yorgunluk
    if sleep <= 4 or fatigue >= 8:
        return 'delta'
    # Kural 4 — akut ruh hali düşüklüğü veya çift stres
    if mood <= 3 or (anxiety >= 6 and stress >= 6):
        return 'alpha'
    # Kural 5 — akut odak sorunu
    if focus <= 3:
        return 'beta'
    # Kural 6 — orta ruh hali veya stres+anksiyete birlikte
    if (anxiety >= 5 and stress >= 5) or mood <= 4:
        return 'alpha'
    # Kural 7 — orta odak veya belirgin yorgunluk
    if focus <= 4 or fatigue >= 7:
        return 'beta'
    # Kural 8 — genel iyilik
    if sleep >= 7 and stress <= 4 and focus >= 7 and mood >= 7 and anxiety <= 4 and fatigue <= 4:
        return 'gamma'

    # Fallback: her frekans için numerik ihtiyaç skoru
    deficits = {
        'delta': max(0, 5 - sleep) * 1.5 + max(0, fatigue - 5) * 0.5,
        'theta': max(0, anxiety - 4) + max(0, stress - 4),
        'alpha': max(0, 5 - mood) + max(0, anxiety - 3) * 0.5,
        'beta':  max(0, 5 - focus) + max(0, fatigue - 5) * 0.5,
        'gamma': float(
            sleep + focus + mood - stress - anxiety - fatigue > 6
        ),
    }
    return max(deficits, key=deficits.get)


def generate_training_data(n_samples=15000, noise_rate=0.02, seed=42):
    """
    (X, y) döndürür.
    X: shape (n_samples, 6) — [sleep, stress, focus, mood, anxiety, fatigue]
    y: list of str — frekans etiketi
    """
    rng = np.random.default_rng(seed)

    data = rng.integers(1, 11, size=(n_samples, 6))
    sleep   = data[:, 0]
    stress  = data[:, 1]
    focus   = data[:, 2]
    mood    = data[:, 3]
    anxiety = data[:, 4]
    fatigue = data[:, 5]

    labels = [
        _label(sleep[i], stress[i], focus[i], mood[i], anxiety[i], fatigue[i])
        for i in range(n_samples)
    ]

    # %2 gürültü — overfitting önlemi
    noise_indices = np.where(rng.random(n_samples) < noise_rate)[0]
    for idx in noise_indices:
        labels[idx] = rng.choice(FREQUENCY_LABELS)

    return data.astype(np.float32), labels
