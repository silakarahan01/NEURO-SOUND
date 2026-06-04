"""
Frekans öneri ML modelini yeniden eğitir ve kaydeder.

Kullanım:
    python manage.py train_ml_model
    python manage.py train_ml_model --samples 5000
"""
from django.core.management.base import BaseCommand

from main.ml.recommender import train_and_save


class Command(BaseCommand):
    help = "Frekans öneri ML modelini sentetik verilerle yeniden eğitir."

    def add_arguments(self, parser):
        parser.add_argument(
            '--samples',
            type=int,
            default=15000,
            help='Eğitim için sentetik örnek sayısı (varsayılan: 15000)',
        )

    def handle(self, *args, **options):
        n = options['samples']
        self.stdout.write(f"{n} örnek ile model eğitiliyor...")
        train_and_save(n_samples=n)
        self.stdout.write(self.style.SUCCESS("Model başarıyla eğitildi ve kaydedildi."))
