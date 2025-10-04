# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20250926_0652'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otploginsession',
            name='attempts',
        ),
        migrations.RemoveField(
            model_name='otploginsession',
            name='ip',
        ),
        migrations.RemoveField(
            model_name='otploginsession',
            name='user_agent',
        ),
    ]

