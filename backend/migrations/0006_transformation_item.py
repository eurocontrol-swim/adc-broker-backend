# Generated by Django 3.2.9 on 2021-11-29 09:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_auto_20211126_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='TRANSFORMATION_ITEM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_schema', models.CharField(max_length=500)),
                ('data_path', models.CharField(max_length=500)),
                ('item_type', models.CharField(choices=[('Organization type', 'organization_type'), ('Organization name', 'organization_name'), ('Data based', 'data_based')], default='Organization type', max_length=255, verbose_name='item_type')),
                ('item_operator', models.CharField(choices=[('Endpoint restriction', 'endpoint_restriction'), ('Payload extraction', 'payload_extraction')], default='Endpoint restriction', max_length=255, verbose_name='item_operator')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.organizations')),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.publisher_policy')),
            ],
        ),
    ]
