# Generated by Django 4.2.1 on 2023-06-04 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_sorderdetail_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='grndetail',
            name='expiry',
            field=models.DateField(blank=True, null=True, verbose_name='expiry'),
        ),
    ]
