# Generated by Django 3.2.9 on 2021-11-29 16:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_transformation_item'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transformation_item',
            old_name='data_path',
            new_name='json_path',
        ),
        migrations.RemoveField(
            model_name='transformation_item',
            name='policy',
        ),
        migrations.AddField(
            model_name='transformation_item',
            name='item_order',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='transformation_item',
            name='publisher_policy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.publisher_policy'),
        ),
        migrations.AddField(
            model_name='transformation_item',
            name='subscriber_policy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.subscriber_policy'),
        ),
    ]
