#!/bin/bash

# ==============================================================================
# INSTALLATION PROPRE AVEC SUDO (Debian 12 / Ubuntu)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#      INSTALLATION COMPLETE (MODE ADMIN/SUDO)           #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# 1. Mise à jour et installation des outils système
# C'est ici que le sudo est utile : on installe le module venv manquant sur Debian
echo -e "\n${YELLOW}--- 1. Installation des dépendances système (Mot de passe requis) ---${NC}"

sudo apt-get update
# On installe :
# - python3-venv : Pour créer l'environnement virtuel (le truc qui manquait)
# - python3-dev & libpq-dev : Pour compiler psycopg2 correctement
# - postgresql-client : Pour avoir la commande 'psql'
sudo apt-get install -y python3-venv python3-pip python3-dev libpq-dev postgresql-client

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de l'installation système via apt-get.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Outils système installés.${NC}"

# 2. Création de l'environnement virtuel (VENV)
echo -e "\n${YELLOW}--- 2. Création de l'environnement virtuel ---${NC}"

# On supprime l'ancien s'il existe pour repartir à neuf
rm -rf venv

# Maintenant que python3-venv est installé par apt, cette commande va marcher !
python3 -m venv venv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dossier venv créé avec succès.${NC}"
else
    echo -e "${RED}❌ Erreur lors de la création du venv.${NC}"
    exit 1
fi

# 3. Installation des librairies Python DANS le venv
echo -e "\n${YELLOW}--- 3. Installation des librairies Python ---${NC}"

# On utilise le pip qui est DANS le dossier venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install flask psycopg2-binary python-dotenv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Flask et Psycopg2 installés dans l'environnement virtuel.${NC}"
else
    echo -e "${RED}❌ Erreur pip.${NC}"
    exit 1
fi

# 4. Création du lanceur
echo -e "\n${YELLOW}--- 4. Configuration du démarrage ---${NC}"

cat <<EOT > run.sh
#!/bin/bash
# Active l'environnement virtuel et lance le serveur
source venv/bin/activate
echo "🚀 Lancement du serveur Agenda..."
python3 app.py
EOT

chmod +x run.sh

# 5. Gitignore
if [ ! -f ".gitignore" ]; then
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo "agenda.db" >> .gitignore
    echo ".env" >> .gitignore
fi

echo -e "${GREEN}✅ TERMINÉ !${NC}"
echo -e "👉 Lance ton projet avec : ${YELLOW}./run.sh${NC}"
