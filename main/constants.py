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
        'description': 'Deep sleep, regeneration, and dreamless rest',
        'color': 'violet',  # semantic color for future reference
        'icon_class': 'fa-moon',
        'tailwind_classes': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
        'benefits': [
            'Promotes deep, restorative sleep',
            'Enhances physical healing and recovery',
            'Reduces stress and anxiety',
        ],
        'duration_minutes': 30,
    },
    'theta': {
        'name': 'Theta',
        'frequency': '4-8 Hz',
        'description': 'Meditation, creativity, and light sleep',
        'color': 'blue',
        'icon_class': 'fa-wind',
        'tailwind_classes': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        'benefits': [
            'Enhances creativity and imagination',
            'Supports deep meditation',
            'Facilitates learning and memory',
        ],
        'duration_minutes': 30,
    },
    'alpha': {
        'name': 'Alpha',
        'frequency': '8-12 Hz',
        'description': 'Relaxation, focus, and calm awareness',
        'color': 'cyan',
        'icon_class': 'fa-spa',
        'tailwind_classes': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
        'benefits': [
            'Promotes relaxation and calm',
            'Enhances focus and concentration',
            'Improves mood and reduces anxiety',
        ],
        'duration_minutes': 25,
    },
    'beta': {
        'name': 'Beta',
        'frequency': '12-30 Hz',
        'description': 'Active thinking, alertness, and energy',
        'color': 'green',
        'icon_class': 'fa-bolt',
        'tailwind_classes': 'bg-green-500/10 text-green-400 border-green-500/20',
        'benefits': [
            'Boosts alertness and focus',
            'Increases mental energy',
            'Supports productive work and study',
        ],
        'duration_minutes': 20,
    },
    'gamma': {
        'name': 'Gamma',
        'frequency': '30-100 Hz',
        'description': 'Peak cognitive function and insight',
        'color': 'amber',
        'icon_class': 'fa-fire',
        'tailwind_classes': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        'benefits': [
            'Enhances cognitive processing',
            'Promotes problem-solving and insight',
            'Supports peak mental performance',
        ],
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
