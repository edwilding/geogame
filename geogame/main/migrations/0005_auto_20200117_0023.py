# Generated by Django 2.2.4 on 2020-01-17 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20191125_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='average',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='name',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Challenge Name'),
        ),
    ]