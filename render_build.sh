#!/bin/bash

# Installa i pacchetti
pip install -r requirements.txt

# Applica le migrazioni al database
python manage.py migrate

# Raccogli i file statici
python manage.py collectstatic --noinput

#python manage.py runserver
