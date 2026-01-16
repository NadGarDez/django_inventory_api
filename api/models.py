from django.db import models
from django.core.validators import MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre

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
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"
    
    
    
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