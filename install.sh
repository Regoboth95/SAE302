#!/bin/bash

# --- COULEURS POUR LE TEXTE (Pour faire pro) ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- DÉMARRAGE DE L'INSTALLATION DE L'AGENDA COLLABORATIF ---${NC}"

# --- 1. VÉRIFICATION DE PYTHON ---
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erreur : Python3 n'est pas installé.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python3 est présent.${NC}"
fi

# --- 2. TENTATIVE D'INSTALLATION SYSTÈME (Optionnel) ---
# On essaie d'installer les outils système seulement si l'utilisateur a sudo
# Si tu es sur un PC IUT sans droits, cette partie sera sautée ou échouera proprement.
echo -e "${YELLOW}--- Vérification des outils système (PostgreSQL client) ---${NC}"

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ Le client PostgreSQL (psql) est déjà installé.${NC}"
else
    echo -e "${YELLOW}⚠️ psql n'est pas trouvé. Tentative d'installation (mot de passe sudo requis)...${NC}"
    # On essaie d'installer sans forcer, si ça échoue on continue quand même pour la partie Python
    sudo apt-get update && sudo apt-get install -y postgresql-client libpq-dev python3-dev
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Installation système réussie.${NC}"
    else
        echo -e "${RED}❌ Échec de l'installation système (Pas de sudo ?).${NC}"
        echo -e "${YELLOW}👉 Ce n'est pas grave si le serveur PostgreSQL est distant ou déjà installé.${NC}"
    fi
fi

# --- 3. CRÉATION DE L'ENVIRONNEMENT VIRTUEL (VENV) ---
# C'est la partie la plus importante : isole tes libs Python du reste du PC
echo -e "${YELLOW}--- Configuration de l'environnement Python ---${NC}"

if [ ! -d "venv" ]; then
    echo "Création du dossier venv..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé.${NC}"
else
    echo -e "${GREEN}✅ Le dossier venv existe déjà.${NC}"
fi

# --- 4. ACTIVATION ET INSTALLATION DES LIBS ---
echo "Activation de l'environnement et installation des dépendances..."

# On active le venv
source venv/bin/activate

# Mise à jour de pip (le gestionnaire de paquets)
pip install --upgrade pip

# Installation des bibliothèques nécessaires
# Flask : Le serveur Web
# psycopg2-binary : Pour parler à PostgreSQL
# python-dotenv : Pour gérer les variables d'environnement (optionnel mais utile)
pip install flask psycopg2-binary

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Toutes les bibliothèques Python sont installées !${NC}"
else
    echo -e "${RED}❌ Erreur lors de l'installation des bibliothèques.${NC}"
    exit 1
fi

# --- 5. CRÉATION D'UN FICHIER DE LANCEMENT RAPIDE ---
# Crée un petit script 'run.sh' pour ne pas avoir à taper les commandes à chaque fois
echo -e "${YELLOW}--- Création du script de lancement 'run.sh' ---${NC}"

cat <<EOT > run.sh
#!/bin/bash
source venv/bin/activate
echo "🚀 Lancement du serveur Agenda..."
python3 app.py
EOT

chmod +x run.sh

echo -e "${GREEN}✅ Tout est prêt !${NC}"
echo -e "Pour lancer ton application, tape simplement : ${YELLOW}./run.sh${NC}"
