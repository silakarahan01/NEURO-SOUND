"""
Constants for the NEURO SOUND app.
Single source of truth for frequency data and configuration.
"""

# Frequency definitions with semantic names and full Tailwind CSS classes
# This ensures consistency across all templates and eliminates duplication
FREQUENCIES = {
    'delta': {
        'name': 'Delta',
        'frequency': '0.5-4 Hz',
        'description': 'Derin uyku, yenilenme ve rüyasız dinlenme',
        'color': 'violet',  # semantic color for future reference
        'icon_class': 'fa-moon',
        'tailwind_classes': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
        'benefits': [
            'Derin ve onarıcı uykuyu destekler',
            'Fiziksel iyileşme ve toparlanmayı artırır',
            'Stres ve kaygıyı azaltır',
        ],
        'usage': 'Gece yatmadan önce, uykuya geçişi kolaylaştırmak ve derin dinlenme için.',
        'duration_minutes': 30,
    },
    'theta': {
        'name': 'Theta',
        'frequency': '4-8 Hz',
        'description': 'Meditasyon, yaratıcılık ve hafif uyku',
        'color': 'blue',
        'icon_class': 'fa-wind',
        'tailwind_classes': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        'benefits': [
            'Yaratıcılığı ve hayal gücünü güçlendirir',
            'Derin meditasyonu destekler',
            'Öğrenmeyi ve hafızayı kolaylaştırır',
        ],
        'usage': 'Meditasyon, gevşeme ya da yoğun bir günün ardından zihni dinlendirmek için.',
        'duration_minutes': 30,
    },
    'alpha': {
        'name': 'Alpha',
        'frequency': '8-12 Hz',
        'description': 'Rahatlama, odak ve sakin farkındalık',
        'color': 'cyan',
        'icon_class': 'fa-spa',
        'tailwind_classes': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
        'benefits': [
            'Rahatlamayı ve sakinliği teşvik eder',
            'Odak ve konsantrasyonu artırır',
            'Ruh halini iyileştirir ve kaygıyı azaltır',
        ],
        'usage': 'Stresli anlarda sakinleşmek veya sakin bir odakla çalışmak için.',
        'duration_minutes': 25,
    },
    'beta': {
        'name': 'Beta',
        'frequency': '12-30 Hz',
        'description': 'Aktif düşünme, uyanıklık ve enerji',
        'color': 'green',
        'icon_class': 'fa-bolt',
        'tailwind_classes': 'bg-green-500/10 text-green-400 border-green-500/20',
        'benefits': [
            'Uyanıklığı ve odağı artırır',
            'Zihinsel enerjiyi yükseltir',
            'Verimli çalışma ve ders çalışmayı destekler',
        ],
        'usage': 'Çalışırken, ders çalışırken veya yüksek konsantrasyon gerektiren işlerde.',
        'duration_minutes': 20,
    },
    'gamma': {
        'name': 'Gamma',
        'frequency': '30-100 Hz',
        'description': 'Zirve bilişsel işlev ve içgörü',
        'color': 'amber',
        'icon_class': 'fa-fire',
        'tailwind_classes': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        'benefits': [
            'Bilişsel işlemeyi güçlendirir',
            'Problem çözme ve içgörüyü destekler',
            'Zirve zihinsel performansı destekler',
        ],
        'usage': 'Karmaşık problemleri çözerken veya en yüksek zihinsel performans için.',
        'duration_minutes': 15,
    },
}

# List of frequency keys in order
FREQUENCY_CHOICES_LIST = [
    ('delta', 'Delta (0.5-4 Hz) - Deep Sleep'),
    ('theta', 'Theta (4-8 Hz) - Meditation'),
    ('alpha', 'Alpha (8-12 Hz) - Relaxation'),
    ('beta', 'Beta (12-30 Hz) - Focus'),
    ('gamma', 'Gamma (30-100 Hz) - Peak Performance'),
]

# Tuple format for Django model choices
FREQUENCY_CHOICES = tuple(FREQUENCY_CHOICES_LIST)

# Color mappings for UI (semantic to Tailwind colors)
COLOR_CHOICES = [
    ('violet', 'Violet'),
    ('blue', 'Blue'),
    ('cyan', 'Cyan'),
    ('green', 'Green'),
    ('amber', 'Amber'),
]

# Subscription pricing (moved from hardcoded view)
SUBSCRIPTION_PRICES = {
    'INDIVIDUAL': 50.00,
    'PSYCHOLOGIST': 500.00,
}

# Verification code expiry time in minutes
VERIFICATION_CODE_EXPIRY_MINUTES = 15

# Maximum duration for a listening session in minutes
MAX_SESSION_DURATION = 120
