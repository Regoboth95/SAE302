#!/bin/bash

# ==============================================================================
# CONFIGURATION
# ==============================================================================
PYTHON_LIBRARIES="flask psycopg2-binary python-dotenv"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#   INSTALLATION (MODE COMPATIBILITÉ IUT SANS SUDO)      #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# --- 1. VÉRIFICATION PYTHON ---
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Erreur : Python3 n'est pas installé.${NC}"
    exit 1
fi

# --- 2. TENTATIVE DE CRÉATION DU VENV ---
echo -e "\n${YELLOW}--- Tentative de création de l'environnement virtuel ---${NC}"

# On teste si on peut créer un venv
python3 -m venv venv 2> /dev/null

if [ $? -eq 0 ]; then
    # CAS A : Ça marche (votre collègue ou un PC bien configuré)
    echo -e "${GREEN}✅ Environnement virtuel standard créé.${NC}"
    MODE="VENV"
else
    # CAS B : Ça plante (PC IUT sans python3-venv)
    echo -e "${RED}⚠️ Impossible de créer un dossier venv (module manquant).${NC}"
    echo -e "${YELLOW}👉 Passage en mode 'Installation Utilisateur' (Solution de secours)...${NC}"
    MODE="USER"
fi

# --- 3. INSTALLATION DES BIBLIOTHÈQUES ---
echo -e "\n${YELLOW}--- Installation des librairies ($MODE) ---${NC}"

if [ "$MODE" == "VENV" ]; then
    # Méthode standard
    source venv/bin/activate
    pip install --upgrade pip
    pip install $PYTHON_LIBRARIES
else
    # Méthode de secours (Force l'installation dans le dossier perso de l'étudiant)
    # Le flag --break-system-packages est nécessaire sur les Linux récents
    pip install --user $PYTHON_LIBRARIES --break-system-packages
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Bibliothèques installées avec succès !${NC}"
else
    echo -e "${RED}❌ Échec de l'installation des bibliothèques.${NC}"
    exit 1
fi

# --- 4. CRÉATION DU FICHIER DE LANCEMENT ADAPTÉ ---
echo -e "\n${YELLOW}--- Configuration du lanceur run.sh ---${NC}"

if [ "$MODE" == "VENV" ]; then
    # Lanceur pour mode Venv
cat <<EOT > run.sh
#!/bin/bash
source venv/bin/activate
echo "🚀 Lancement (Mode VENV)..."
python3 app.py
EOT
else
    # Lanceur pour mode Utilisateur
cat <<EOT > run.sh
#!/bin/bash
echo "🚀 Lancement (Mode USER)..."
python3 app.py
EOT
fi

chmod +x run.sh

# --- 5. PROTECTION GIT ---
if [ ! -f ".gitignore" ]; then
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo ".env" >> .gitignore
    echo "agenda.db" >> .gitignore
fi

echo -e "${GREEN}✅ TERMINÉ !${NC}"
echo -e "👉 Lancez votre site avec : ${YELLOW}./run.sh${NC}"
