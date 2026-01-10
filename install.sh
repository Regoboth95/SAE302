#!/bin/bash

# ==============================================================================
# INSTALLATION INTELLIGENTE (AUTO-FAILOVER)
# ==============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LIBS="flask psycopg2-binary python-dotenv"

echo -e "${BLUE}##########################################################${NC}"
echo -e "${BLUE}#            INSTALLATION AUTOMATISÉE                    #${NC}"
echo -e "${BLUE}##########################################################${NC}"

# Nettoyage préventif
rm -f run.sh

# --- ÉTAPE 1 : TENTATIVE D'INSTALLATION SYSTÈME (SUDO) ---
echo -e "\n${YELLOW}--- 1. Tentative de configuration système ---${NC}"
echo "Le script va essayer d'utiliser 'sudo'. Si vous n'avez pas le mot de passe,"
echo "appuyez simplement sur ENTRÉE ou laissez l'erreur se produire."

# On tente l'installation système.
# Le "2> /dev/null" cache les messages d'erreurs moches si ça rate.
sudo apt-get update 2> /dev/null
sudo apt-get install -y python3-venv python3-pip python3-dev libpq-dev postgresql-client 2> /dev/null

# On vérifie le code de retour de la dernière commande ($?)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Succès : Droits administrateur détectés. Outils installés.${NC}"
    SYSTEM_INSTALL=true
else
    echo -e "${RED}❌ Échec sudo (Pas de droits ou mot de passe incorrect).${NC}"
    echo -e "${YELLOW}👉 Pas de panique ! Passage automatique en mode 'Installation Locale'.${NC}"
    SYSTEM_INSTALL=false
fi

# --- ÉTAPE 2 : PRÉPARATION DE L'ENVIRONNEMENT PYTHON ---
echo -e "\n${YELLOW}--- 2. Installation des bibliothèques Python ---${NC}"

# On nettoie un éventuel venv cassé
rm -rf venv

# On tente de créer le VENV (Environnement Virtuel)
# Cela marchera si SYSTEM_INSTALL=true, mais échouera probablement sinon.
python3 -m venv venv 2> /dev/null

if [ $? -eq 0 ]; then
    # --- CAS A : SUCCÈS (Le venv fonctionne) ---
    echo -e "${GREEN}✅ Environnement virtuel (venv) créé.${NC}"
    
    ./venv/bin/pip install --upgrade pip > /dev/null
    ./venv/bin/pip install $LIBS
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Bibliothèques installées dans le venv.${NC}"
        
        # Création du run.sh pour VENV
        cat <<EOT > run.sh
#!/bin/bash
source venv/bin/activate
echo "🚀 Lancement (Mode VENV)..."
python3 app.py
EOT
    else
        echo -e "${RED}❌ Erreur bizarre lors du pip install dans le venv.${NC}"
        exit 1
    fi

else
    # --- CAS B : ÉCHEC (Venv impossible -> Installation locale) ---
    echo -e "${YELLOW}⚠️ Impossible de créer le venv (Module manquant).${NC}"
    echo -e "${YELLOW}👉 Installation directe dans votre dossier utilisateur...${NC}"
    
    # 1. Tentative avec le flag moderne (Debian 12 / Ubuntu récents)
    pip3 install --user $LIBS --break-system-packages > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Bibliothèques installées (Mode --break-system-packages).${NC}"
    else
        # 2. Tentative classique (Vieux Ubuntu) si le flag n'est pas reconnu
        pip3 install --user $LIBS > /dev/null 2>&1
        if [ $? -eq 0 ]; then
             echo -e "${GREEN}✅ Bibliothèques installées (Mode classique).${NC}"
        else
             echo -e "${RED}❌ Impossible d'installer les bibliothèques. Vérifiez votre connexion internet.${NC}"
             exit 1
        fi
    fi
    
    # Création du run.sh pour USER
    cat <<EOT > run.sh
#!/bin/bash
# Ajout du chemin local au PATH (souvent nécessaire quand on installe en --user)
export PATH=\$PATH:\$HOME/.local/bin
echo "🚀 Lancement (Mode USER)..."
python3 app.py
EOT
fi

chmod +x run.sh

# --- ÉTAPE 3 : FINITION ---
if [ ! -f ".gitignore" ]; then
    echo "venv/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo ".env" >> .gitignore
    echo "agenda.db" >> .gitignore
fi

echo -e "\n${GREEN}✅ INSTALLATION TERMINÉE !${NC}"
echo -e "👉 Lancez le site avec : ${YELLOW}./run.sh${NC}"
