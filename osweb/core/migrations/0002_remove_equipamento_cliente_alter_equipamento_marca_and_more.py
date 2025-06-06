# Generated by Django 5.2 on 2025-05-04 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipamento',
            name='cliente',
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='marca',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='numero_serie',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='tipo',
            field=models.CharField(max_length=100),
        ),
    ]
