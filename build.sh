#!/usr/bin/env bash
# Script exécuté par Render au déploiement

set -o errexit

# Installer les dépendances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations
python manage.py migrate

# Créer un superuser automatiquement si les variables d'env sont définies
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@aqualynk.sn')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Aqualynk2026Admin')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} cree avec succes')
else:
    print(f'Superuser {username} existe deja')
"