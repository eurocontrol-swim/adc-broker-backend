# Generated by Django 3.2.9 on 2021-11-26 14:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0002_user_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_info',
            name='user_role',
            field=models.CharField(choices=[('Administrator', 'Administrator'), ('Publisher', 'Publisher'), ('Subscriber', 'Subscriber')], default='Subscriber', max_length=255, verbose_name='user_role'),
        ),
        migrations.CreateModel(
            name='SUBSCRIBER_POLICY',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
