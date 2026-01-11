#!/bin/bash

# ==============================================================================
# INSTALLATION COMPLÈTE (PYTHON + BASE DE DONNÉES V2)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#      INSTALLATION AUTOMATISÉE DE L'AGENDA (V2)         #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# --- ÉTAPE 1 : PYTHON & LIBRAIRIES ---
echo -e "\n${YELLOW}--- 1. Configuration Python ---${NC}"

# Nettoyage
rm -rf venv run.sh

# Création venv
python3 -m venv venv 2> /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Venv créé.${NC}"
    ./venv/bin/pip install --upgrade pip > /dev/null
    ./venv/bin/pip install flask psycopg2-binary > /dev/null
    CMD_PYTHON="./venv/bin/python3"
else
    echo -e "${YELLOW}⚠️ Venv impossible. Installation utilisateur.${NC}"
    pip3 install --user flask psycopg2-binary --break-system-packages > /dev/null 2>&1 || pip3 install --user flask psycopg2-binary
    CMD_PYTHON="python3"
fi

# --- ÉTAPE 2 : CONFIGURATION BASE DE DONNÉES ---
echo -e "\n${YELLOW}--- 2. Configuration PostgreSQL ---${NC}"

# A. Création Utilisateur et Database (Nécessite Sudo)
# Cette partie crée l'utilisateur 'app_agenda_user' et la BDD si elles n'existent pas
if sudo -n true 2>/dev/null || sudo -v 2>/dev/null; then
    echo "Droits Sudo détectés. Vérification du compte et de la BDD..."
    sudo -u postgres psql -c "CREATE USER app_agenda_user WITH PASSWORD 'Azerty@123';" 2>/dev/null || echo "   -> Utilisateur déjà présent."
    sudo -u postgres psql -c "CREATE DATABASE agenda_collaboratif OWNER app_agenda_user;" 2>/dev/null || echo "   -> Base de données déjà présente."
else
    echo -e "${YELLOW}⚠️ Pas de droits Sudo : Assurez-vous que la BDD 'agenda_collaboratif' existe déjà.${NC}"
fi

# B. Création des Tables via le script Python (Remplace le fichier .sql)
echo -e "Injection des tables (V1 + Historique V2)..."

if [ -f "init_db.py" ]; then
    # C'est ICI que la magie opère : on lance le script Python qu'on a créé juste avant
    $CMD_PYTHON init_db.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tables initialisées avec succès !${NC}"
    else
        echo -e "${RED}❌ Erreur lors de l'exécution de init_db.py${NC}"
    fi
else
    echo -e "${RED}❌ ERREUR : Le fichier 'init_db.py' est introuvable !${NC}"
fi

# --- ÉTAPE 3 : FINITION ---
cat <<EOT > run.sh
#!/bin/bash
echo "🚀 Lancement..."
$CMD_PYTHON app.py
EOT
chmod +x run.sh

echo -e "\n${GREEN}✅ INSTALLATION TERMINÉE !${NC}"
echo -e "👉 Lancez : ${YELLOW}./run.sh${NC}"
