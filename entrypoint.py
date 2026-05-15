#!/usr/bin/env python
"""Entrypoint script for Docker container."""
import os
import sys
import time
import subprocess


def wait_for_db():
    """Wait for PostgreSQL to be ready."""
    import psycopg2
    print("Esperando a que PostgreSQL este listo...")
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                host=os.environ.get('DB_HOST'),
                port=os.environ.get('DB_PORT'),
            )
            conn.close()
            print("PostgreSQL listo!")
            return True
        except psycopg2.OperationalError:
            print(f"PostgreSQL no disponible, reintentando en 2s... ({i+1}/{max_retries})")
            time.sleep(2)
    print("ERROR: No se pudo conectar a PostgreSQL")
    return False


def run_migrations():
    """Run Django migrations."""
    print("Aplicando migraciones...")
    subprocess.run([sys.executable, "manage.py", "makemigrations", "--noinput"], check=True)
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
    print("Migraciones aplicadas correctamente!")


def create_superuser():
    """Create default superuser if it doesn't exist."""
    print("Verificando superusuario...")
    code = (
        "from django.contrib.auth.models import User; "
        "created = not User.objects.filter(username='admin').exists() and "
        "User.objects.create_superuser('admin', 'admin@encomiendas.com', 'admin123'); "
        "print('Superusuario creado: admin / admin123' if created else 'Superusuario ya existe')"
    )
    subprocess.run([sys.executable, "manage.py", "shell", "-c", code], check=True)


def start_server():
    """Start Django development server."""
    print("Iniciando servidor Django...")
    os.execvp(sys.executable, [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])


if __name__ == "__main__":
    if wait_for_db():
        run_migrations()
        create_superuser()
        start_server()
    else:
        sys.exit(1)
