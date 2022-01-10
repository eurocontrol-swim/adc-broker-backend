# Generated by Django 3.2.9 on 2022-01-10 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0023_alter_transformation_item_item_operator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transformation_item',
            name='item_operator',
            field=models.CharField(choices=[('Organization name endpoint restriction', 'organization_name_endpoint_restriction'), ('Organization type endpoint restriction', 'organization_type_endpoint_restriction'), ('Payload extraction', 'payload_extraction')], max_length=255, null=True, verbose_name='item_operator'),
        ),
    ]