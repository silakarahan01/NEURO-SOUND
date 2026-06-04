from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_prescription_patient_limit_fix'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Ad Soyad')),
                ('email', models.EmailField(max_length=254, verbose_name='E-posta')),
                ('message', models.TextField(verbose_name='Mesaj')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False, verbose_name='Okundu mu?')),
            ],
            options={
                'verbose_name': 'İletişim Mesajı',
                'verbose_name_plural': 'İletişim Mesajları',
                'ordering': ['-created_at'],
            },
        ),
    ]
