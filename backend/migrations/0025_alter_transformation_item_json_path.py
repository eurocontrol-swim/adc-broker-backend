# Generated by Django 3.2.9 on 2022-01-10 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0024_alter_transformation_item_item_operator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transformation_item',
            name='json_path',
            field=models.CharField(max_length=500, null=True),
        ),
    ]