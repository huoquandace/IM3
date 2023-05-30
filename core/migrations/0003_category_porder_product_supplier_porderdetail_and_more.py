# Generated by Django 4.2.1 on 2023-05-29 16:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_profile_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('label', models.CharField(max_length=255, verbose_name='label')),
                ('image', models.ImageField(upload_to='category', verbose_name='image')),
                ('description', models.TextField(verbose_name='description')),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='POrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(blank=True, max_length=255, null=True, verbose_name='label')),
                ('order_date', models.DateField(blank=True, null=True, verbose_name='order date')),
                ('status', models.CharField(blank=True, default='draft', max_length=255, null=True, verbose_name='status')),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('total', models.IntegerField(blank=True, null=True, verbose_name='total')),
                ('note', models.TextField(blank=True, null=True, verbose_name='note')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_product', models.CharField(max_length=255, verbose_name='product id')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('brand', models.CharField(max_length=255, verbose_name='brand')),
                ('image', models.ImageField(upload_to='product', verbose_name='image')),
                ('price', models.IntegerField(verbose_name='price')),
                ('description', models.TextField(verbose_name='description')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.category', verbose_name='category')),
            ],
            options={
                'verbose_name_plural': 'products',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_supplier', models.CharField(max_length=255, verbose_name='supplier id')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='supplier', verbose_name='logo')),
                ('phone', models.CharField(max_length=255, verbose_name='phone')),
                ('address', models.TextField(verbose_name='address')),
                ('fax', models.CharField(max_length=255, verbose_name='fax')),
                ('email', models.EmailField(max_length=255, verbose_name='email')),
                ('account', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='account')),
                ('products', models.ManyToManyField(blank=True, to='core.product', verbose_name='products')),
            ],
        ),
        migrations.CreateModel(
            name='POrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(blank=True, default=1, null=True, verbose_name='quantity')),
                ('price', models.IntegerField(blank=True, null=True, verbose_name='price')),
                ('status', models.CharField(blank=True, max_length=255, null=True, verbose_name='status')),
                ('porder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.porder', verbose_name='purchare order')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.product', verbose_name='product')),
            ],
        ),
        migrations.AddField(
            model_name='porder',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.supplier', verbose_name='supplier'),
        ),
    ]
