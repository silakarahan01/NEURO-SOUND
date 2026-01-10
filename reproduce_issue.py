import os
import django
from django.conf import settings
from django.template import Template, Context, Engine
from django.template.loader import render_to_string

# Configure Django settings manually
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if not settings.configured:
    settings.configure(
        DEBUG=True,
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'APP_DIRS': True,
        }],
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'neuro_core', # Assuming this is the app name based on folder structure
        ]
    )
    django.setup()

def check_template_syntax():
    template_path = 'dashboard/patient_dashboard.html'
    try:
        # Try to load the template to check for syntax errors
        render_to_string(template_path)
        print("Template syntax is valid.")
    except Exception as e:
        print(f"Template Syntax Error Found:\n{e}")

if __name__ == "__main__":
    check_template_syntax()
