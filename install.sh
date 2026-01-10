#!/bin/bash

# ==============================================================================
# INSTALLATION COMPLÈTE (PYTHON + BASE DE DONNÉES)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#      INSTALLATION AUTOMATISÉE DE L'AGENDA              #${NC}"
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
    ./venv/bin/pip install flask psycopg2-binary python-dotenv > /dev/null
    CMD_PYTHON="./venv/bin/python3"
else
    echo -e "${YELLOW}⚠️ Venv impossible. Installation utilisateur.${NC}"
    pip3 install --user flask psycopg2-binary python-dotenv --break-system-packages > /dev/null 2>&1 || pip3 install --user flask psycopg2-binary python-dotenv
    CMD_PYTHON="python3"
fi

# --- ÉTAPE 2 : CONFIGURATION BASE DE DONNÉES (AUTO) ---
echo -e "\n${YELLOW}--- 2. Configuration PostgreSQL ---${NC}"

# On vérifie si on a le fichier SQL sous la main
if [ ! -f "agenda_collab_db.sql" ]; then
    echo -e "${RED}❌ ERREUR : Le fichier 'agenda_collab_db.sql' est introuvable !${NC}"
    echo "Impossible d'initialiser la base de données sans ce fichier."
else
    # On teste si on a sudo pour configurer postgres
    if sudo -n true 2>/dev/null || sudo -v 2>/dev/null; then
        echo "Droits Sudo détectés. Configuration de la BDD..."

        # 1. Création de l'utilisateur (ignore l'erreur s'il existe déjà)
        sudo -u postgres psql -c "CREATE USER app_agenda_user WITH PASSWORD 'Azerty@123';" 2>/dev/null || echo "   -> L'utilisateur existe déjà."

        # 2. Création de la BDD (ignore l'erreur si elle existe déjà)
        sudo -u postgres psql -c "CREATE DATABASE agenda_collaboratif OWNER app_agenda_user;" 2>/dev/null || echo "   -> La base existe déjà."

        # 3. Injection des tables depuis le fichier SQL
        echo "Injection des tables..."
        # L'export permet d'éviter que psql demande le mot de passe
        export PGPASSWORD='Azerty@123'
        psql -h localhost -U app_agenda_user -d agenda_collaboratif -f agenda_collab_db.sql > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Tables créées avec succès !${NC}"
        else
            echo -e "${RED}❌ Erreur lors de l'injection SQL (Vérifiez le fichier .sql).${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Pas de droits Sudo : La configuration BDD automatique est sautée.${NC}"
        echo "Vous devrez créer la base manuellement ou utiliser SQLite."
    fi
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
