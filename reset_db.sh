#!/bin/bash
# 1. Création de l'utilisateur PostgreSQL
sudo -u postgres psql -c "CREATE USER app_agenda_user WITH PASSWORD 'Azerty@123';"

# 2. Création de la Base de données
sudo -u postgres psql -c "CREATE DATABASE agenda_collaboratif OWNER app_agenda_user;"

# 3. Lancement du script SQL
# (Assurez-vous que le fichier .sql est dans le même dossier)
sudo -u postgres psql -d agenda_collaboratif -f agenda_collab_db.sql
