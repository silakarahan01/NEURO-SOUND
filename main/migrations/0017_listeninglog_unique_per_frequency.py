from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_alter_user_managers'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='listeninglog',
            unique_together={('user', 'date', 'frequency')},
        ),
    ]
