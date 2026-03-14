from django.db import models
from django.core.validators import MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from decimal import Decimal

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    precio_compra_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    precio_venta_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

    @property
    def stock_actual(self):
        stock = getattr(self, 'stock', None)
        if stock is not None:
            return stock.cantidad
        return 0

    @property
    def valor_inventario_compra(self):
        return self.precio_compra_actual * self.stock_actual

    @property
    def valor_inventario_venta(self):
        return self.precio_venta_actual * self.stock_actual

class Existencia(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='stock')
    cantidad = models.PositiveIntegerField(default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.producto.nombre}: {self.cantidad} unidades"

class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada (Compra/Ajuste)'),
        ('SALIDA', 'Salida (Venta/Ajuste)'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='transacciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario_historico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"

    @property
    def valor_movimiento(self):
        return self.precio_unitario_historico * self.cantidad

    def save(self, *args, **kwargs):
        if self._state.adding and self.precio_unitario_historico == Decimal('0.00'):
            if self.tipo == 'ENTRADA':
                self.precio_unitario_historico = self.producto.precio_compra_actual
            elif self.tipo == 'SALIDA':
                self.precio_unitario_historico = self.producto.precio_venta_actual
        super().save(*args, **kwargs)
    
    
    
@receiver(post_save, sender=Transaccion)
def actualizar_stock(sender, instance, created, **kwargs):
    print("Se ha guardado una transacción:", instance)
    if created:
        # Obtenemos o creamos el registro de existencia para el producto
        existencia, _ = Existencia.objects.get_or_create(producto=instance.producto)
        
        if instance.tipo == 'ENTRADA':
            existencia.cantidad += instance.cantidad
        elif instance.tipo == 'SALIDA':
            # Aquí podrías agregar lógica para evitar stock negativo si lo deseas
            existencia.cantidad -= instance.cantidad
        
        existencia.save()
        print(f"Stock actualizado para {instance.producto.nombre}: {existencia.cantidad} unidades")