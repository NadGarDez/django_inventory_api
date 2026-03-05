#!/bin/sh

# Esperar a que la base de datos esté lista (opcional pero recomendado)
echo "Esperando a la base de datos..."

# Ejecutar migraciones
echo "Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate --noinput

# Recolectar archivos estáticos (importante para Nginx)
echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

# Iniciar Gunicorn
echo "Iniciando servidor..."
exec gunicorn inventario.wsgi:application --bind 0.0.0.0:8000 --workers 3