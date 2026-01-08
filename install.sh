#!/bin/bash

# ==============================================================================
# INSTALLATION INTERACTIVE (La seule qui marche à coup sûr)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LIBS="flask psycopg2-binary python-dotenv"

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#            CONFIGURATION DE L'AGENDA                   #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# --- QUESTION CRUCIALE ---
echo ""
echo -e "${YELLOW}Question de configuration :${NC}"
read -p "Avez-vous le mot de passe administrateur (sudo) sur ce PC ? (o/n) : " REPONSE

if [[ "$REPONSE" == "o" || "$REPONSE" == "O" ]]; then
    MODE_ADMIN=true
    echo -e "${GREEN}👉 Mode sélectionné : ADMINISTRATEUR (Installation propre)${NC}"
else
    MODE_ADMIN=false
    echo -e "${YELLOW}👉 Mode sélectionné : UTILISATEUR (Installation locale)${NC}"
fi

# --- ÉTAPE 1 : INSTALLATION SYSTÈME (Seulement si admin) ---
if [ "$MODE_ADMIN" = true ]; then
    echo -e "\n${YELLOW}--- 1. Installation des outils système ---${NC}"
    # On met à jour et on installe le module venv manquant
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip python3-dev libpq-dev postgresql-client
else
    echo -e "\n${YELLOW}--- 1. Pas d'installation système (Ignoré) ---${NC}"
fi

# --- ÉTAPE 2 : PRÉPARATION PYTHON ---
echo -e "\n${YELLOW}--- 2. Installation des bibliothèques Python ---${NC}"

# Nettoyage
rm -rf venv
rm -f run.sh

# On tente de créer le venv (ça marchera chez le collègue, et peut-être chez vous)
python3 -m venv venv 2> /dev/null

if [ $? -eq 0 ]; then
    # --- CAS A : VENV DISPONIBLE ---
    echo -e "${GREEN}✅ Environnement virtuel créé.${NC}"
    
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install $LIBS
    
    # Run.sh pour VENV
    cat <<EOT > run.sh
#!/bin/bash
source venv/bin/activate
echo "🚀 Lancement (Mode VENV)..."
python3 app.py
EOT

else
    # --- CAS B : PAS DE VENV (Votre cas sur Ubuntu sans sudo) ---
    echo -e "${YELLOW}⚠️ Module venv absent. Installation directe dans votre dossier.${NC}"
    
    # On force l'installation locale avec le flag pour les Linux récents
    pip3 install --user $LIBS --break-system-packages > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        # Si le flag n'est pas reconnu (vieux Linux), on tente sans
        pip3 install --user $LIBS
    fi
    
    # Run.sh pour USER
    cat <<EOT > run.sh
#!/bin/bash
export PATH=\$PATH:\$HOME/.local/bin
echo "🚀 Lancement (Mode USER)..."
python3 app.py
EOT
fi

chmod +x run.sh

# --- FINITION ---
if [ ! -f ".gitignore" ]; then
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo ".env" >> .gitignore
fi

echo -e "\n${GREEN}✅ TERMINE !${NC}"
echo -e "👉 Lancez le site avec : ${YELLOW}./run.sh${NC}"
