#!/bin/bash

# ==============================================================================
# SCRIPT D'INSTALLATION UNIVERSEL (Compatible Sudo ET Sans-Sudo)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LIBS="flask psycopg2-binary python-dotenv"

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#           INSTALLATION AUTO-ADAPTATIVE                 #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# --- ETAPE 1 : GESTION DES DEPENDANCES SYSTEME (POUR CELUI QUI A SUDO) ---
echo -e "\n${YELLOW}--- 1. Vérification des droits administrateur (Sudo) ---${NC}"

# On vérifie si l'utilisateur a accès à sudo sans bloquer le script
if command -v sudo >/dev/null 2>&1 && sudo -v >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Droits Sudo détectés (Mode Admin).${NC}"
    echo "Mise à jour et installation des outils manquants..."
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip python3-dev libpq-dev postgresql-client
else
    echo -e "${YELLOW}⚠️ Pas de droits Sudo détectés (Mode Étudiant restreint).${NC}"
    echo "👉 On saute l'installation système et on passe en mode 'Survie'."
fi

# --- ETAPE 2 : TENTATIVE DE CRÉATION DU VENV ---
echo -e "\n${YELLOW}--- 2. Configuration de l'environnement Python ---${NC}"

# On nettoie
rm -rf venv
rm -f run.sh

# On essaie de créer le venv
python3 -m venv venv 2> /dev/null

if [ $? -eq 0 ]; then
    # --- CAS A : SUCCÈS (Le venv a marché) ---
    echo -e "${GREEN}✅ Environnement virtuel créé avec succès.${NC}"
    MODE="VENV"
    
    # Installation dans le venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install $LIBS
    
    # Création du run.sh pour VENV
    cat <<EOT > run.sh
#!/bin/bash
source venv/bin/activate
echo "🚀 Lancement (Mode VENV)..."
python3 app.py
EOT

else
    # --- CAS B : ÉCHEC (Pas de module venv et pas de sudo) ---
    echo -e "${RED}⚠️ Impossible de créer le dossier venv.${NC}"
    echo -e "${YELLOW}👉 Passage automatique en mode 'Installation Utilisateur' (--user).${NC}"
    MODE="USER"
    
    # Installation locale (dans le dossier perso de l'étudiant)
    # On teste avec --break-system-packages (pour Debian 12/Ubuntu récents)
    pip3 install --user $LIBS --break-system-packages > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        # Si ça rate, on tente sans le flag (pour vieux Ubuntu)
        pip3 install --user $LIBS
    fi
    
    # Création du run.sh pour USER
    cat <<EOT > run.sh
#!/bin/bash
# On ajoute le chemin local au PATH au cas où
export PATH=\$PATH:\$HOME/.local/bin
echo "🚀 Lancement (Mode USER)..."
python3 app.py
EOT
fi

chmod +x run.sh

# --- ETAPE 3 : FINITION ---
if [ ! -f ".gitignore" ]; then
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo "agenda.db" >> .gitignore
    echo ".env" >> .gitignore
fi

echo -e "\n${GREEN}✅ INSTALLATION TERMINÉE !${NC}"
echo -e "Mode utilisé : ${YELLOW}$MODE${NC}"
echo -e "👉 Lance
