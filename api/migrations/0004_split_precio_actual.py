from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def copiar_precio_actual(apps, schema_editor):
    Producto = apps.get_model('api', 'Producto')

    for producto in Producto.objects.all():
        precio_actual = producto.precio_actual or Decimal('0.00')
        producto.precio_compra_actual = precio_actual
        producto.precio_venta_actual = precio_actual
        producto.save(update_fields=['precio_compra_actual', 'precio_venta_actual'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_producto_precio_actual_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='precio_compra_actual',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AddField(
            model_name='producto',
            name='precio_venta_actual',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.RunPython(copiar_precio_actual, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='producto',
            name='precio_actual',
        ),
    ]