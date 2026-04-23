#!/bin/bash

echo "Esperando a que PostgreSQL esté listo..."
while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
    echo "PostgreSQL no disponible, reintentando en 2s..."
    sleep 2
done

echo "PostgreSQL listo!"

echo "Aplicando migraciones..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Creando superusuario si no existe..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@encomiendas.com', 'admin123')
    print('Superusuario creado: admin / admin123')
else:
    print('Superusuario ya existe')
"

echo "Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000
