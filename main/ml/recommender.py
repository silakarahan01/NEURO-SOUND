"""
Binaural beat frekans öneri motoru.

Kullanım:
    from main.ml.recommender import recommend
    result = recommend(sleep_quality=3, stress_level=8, focus_level=5,
                       mood_score=5, anxiety_level=7, fatigue_level=6)
    # {'frequency': 'theta', 'minutes': 27, 'days': 18, 'confidence': 0.91}
"""

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR  = Path(__file__).parent / 'models'
MODEL_PATH = MODEL_DIR / 'frequency_model.pkl'

# Klinik dakika aralıkları: (min_dk, max_dk, base_dk)
_MINUTES_RANGE = {
    'delta': (20, 45, 32),
    'theta': (20, 35, 27),
    'alpha': (15, 30, 22),
    'beta':  (15, 25, 20),
    'gamma': (10, 20, 15),
}

_MODEL_CACHE = {}


def _compute_severity(freq_key, features):
    """
    Seçilen frekans için kompozit şiddet skoru (0-1) hesaplar.
    features: [sleep, stress, focus, mood, anxiety, fatigue]  (1-10 arası)
    """
    sleep, stress, focus, mood, anxiety, fatigue = (float(v) for v in features)

    if freq_key == 'delta':
        return 0.60 * (10 - sleep) / 9.0 + 0.40 * fatigue / 9.0
    if freq_key == 'theta':
        return 0.55 * anxiety / 9.0 + 0.45 * stress / 9.0
    if freq_key == 'alpha':
        return 0.50 * (10 - mood) / 9.0 + 0.30 * anxiety / 9.0 + 0.20 * stress / 9.0
    if freq_key == 'beta':
        return 0.60 * (10 - focus) / 9.0 + 0.40 * fatigue / 9.0
    # gamma: bakım amaçlı, düşük şiddet
    return 0.15


def _severity_to_days(severity):
    if severity >= 0.70:
        return 21
    if severity >= 0.50:
        return 18
    if severity >= 0.30:
        return 15
    return 10


def _scale_minutes(freq_key, severity):
    """Şiddete göre dakikayı klinik aralık içinde interpole eder."""
    min_dk, max_dk, _ = _MINUTES_RANGE[freq_key]
    return max(min_dk, min(max_dk, round(min_dk + severity * (max_dk - min_dk))))


def train_and_save(n_samples=8000):
    """Sentetik verilerle modeli eğitir, 5-katlı CV doğrulaması yapar ve kaydeder."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.preprocessing import LabelEncoder

    from .training_data import generate_training_data

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    X, y = generate_training_data(n_samples=n_samples)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced',
    )

    # 5-katlı stratified cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X, y_enc, cv=cv, scoring='accuracy')
    cv_mean = float(cv_scores.mean())
    cv_std  = float(cv_scores.std())
    logger.info(
        "CV doğruluk: %.4f ± %.4f  (min=%.4f, max=%.4f)",
        cv_mean, cv_std, cv_scores.min(), cv_scores.max(),
    )
    if cv_mean < 0.90:
        logger.warning(
            "CV doğruluğu hedefin altında (%.2f%% < 90%%). "
            "Eğitim verisini veya kural ağırlıklarını gözden geçirin.",
            cv_mean * 100,
        )

    clf.fit(X, y_enc)

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump({'clf': clf, 'le': le, 'cv_accuracy': cv_mean}, f)

    _MODEL_CACHE.clear()
    logger.info(
        "ML modeli kaydedildi: %s  |  CV accuracy=%.2f%%",
        MODEL_PATH, cv_mean * 100,
    )
    return cv_mean


def _load_model():
    if 'bundle' not in _MODEL_CACHE:
        if not MODEL_PATH.exists():
            logger.warning("Model bulunamadı — otomatik eğitim başlatılıyor.")
            train_and_save()
        with open(MODEL_PATH, 'rb') as f:
            _MODEL_CACHE['bundle'] = pickle.load(f)
    return _MODEL_CACHE['bundle']


def recommend(sleep_quality, stress_level, focus_level,
              mood_score, anxiety_level, fatigue_level):
    """
    Verilen skorlara göre frekans, günlük dakika ve program süresi önerir.

    Döndürür:
        dict: {
            'frequency':  str,    # 'delta' | 'theta' | 'alpha' | 'beta' | 'gamma'
            'minutes':    int,    # günlük önerilen dakika
            'days':       int,    # program süresi (gün)
            'confidence': float,  # modelin güven skoru (0.0 – 1.0)
        }
    """
    bundle = _load_model()
    clf, le = bundle['clf'], bundle['le']

    features = np.array(
        [[sleep_quality, stress_level, focus_level, mood_score, anxiety_level, fatigue_level]],
        dtype=np.float32,
    )

    # predict_proba tek geçişte hem sınıfı (argmax) hem güveni verir;
    # ayrıca predict() çağırmak ormanı ikinci kez dolaşmak olurdu.
    proba      = clf.predict_proba(features)[0]
    pred_enc   = int(np.argmax(proba))
    confidence = float(proba[pred_enc])
    freq_key   = str(le.inverse_transform([pred_enc])[0])

    severity = _compute_severity(freq_key, features[0])
    minutes  = _scale_minutes(freq_key, severity)
    days     = _severity_to_days(severity)

    return {
        'frequency':  freq_key,
        'minutes':    minutes,
        'days':       days,
        'confidence': confidence,
    }
