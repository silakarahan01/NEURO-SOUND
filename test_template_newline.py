import django
from django.conf import settings
from django.template import Template, Context, Engine

# Minimal Django settings
if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
        }]
    )
    django.setup()

def check_newline_tag():
    print("Testing multiline (should fail to render):")
    template_string = """
    {{ 
        variable 
    }}
    """
    ctx = Context({'variable': 'worked'})
    t = Template(template_string)
    print(f"'{t.render(ctx)}'")

    print("\nTesting single line (should work):")
    template_string_2 = "{{ variable }}"
    t2 = Template(template_string_2)
    print(f"'{t2.render(ctx)}'")

if __name__ == "__main__":
    check_newline_tag()
