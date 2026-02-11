#!/bin/bash

echo "========================================"
echo "Installation de Freebet Optimizer"
echo "========================================"
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERREUR]${NC} Python 3 n'est pas installé"
    echo "Veuillez installer Python 3.8+ :"
    echo "  - Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  - macOS: brew install python3"
    echo "  - Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python est installé"
python3 --version
echo ""

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}[ERREUR]${NC} pip n'est pas installé"
    echo "Installation de pip..."
    python3 -m ensurepip --upgrade
fi

echo -e "${GREEN}[OK]${NC} pip est installé"
echo ""

# Créer un environnement virtuel
echo "Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}[OK]${NC} Environnement virtuel créé"
else
    echo -e "${YELLOW}[INFO]${NC} Environnement virtuel déjà existant"
fi
echo ""

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
echo ""

# Mettre à jour pip
echo "Mise à jour de pip..."
pip install --upgrade pip
echo ""

# Installer les dépendances
echo "Installation des dépendances Python..."
pip install -r requirements.txt
echo ""

# Installer Chrome/Chromium selon l'OS
echo "========================================"
echo "Vérification de Chrome/Chromium"
echo "========================================"
echo ""

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null && ! command -v google-chrome &> /dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Chrome/Chromium n'est pas installé"
        echo "Installation de Chromium..."
        
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y chromium-browser chromium-chromedriver
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y chromium chromium-chromedriver
        elif command -v yum &> /dev/null; then
            sudo yum install -y chromium chromium-chromedriver
        else
            echo -e "${YELLOW}[ATTENTION]${NC} Veuillez installer Chrome/Chromium manuellement"
        fi
    else
        echo -e "${GREEN}[OK]${NC} Chrome/Chromium est installé"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v google-chrome &> /dev/null && ! command -v chromium &> /dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Chrome n'est pas installé"
        echo "Installation via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install --cask google-chrome
        else
            echo -e "${YELLOW}[ATTENTION]${NC} Veuillez installer Chrome manuellement depuis https://www.google.com/chrome/"
        fi
    else
        echo -e "${GREEN}[OK]${NC} Chrome est installé"
    fi
fi

echo ""
echo -e "${YELLOW}[INFO]${NC} Le webdriver sera téléchargé automatiquement au premier lancement"
echo ""

# Créer un fichier de lancement rapide
echo "Création du fichier de lancement..."
cat > start_app.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run app.py
EOF

chmod +x start_app.sh
echo -e "${GREEN}[OK]${NC} Fichier start_app.sh créé"
echo ""

echo "========================================"
echo "Installation terminée avec succès !"
echo "========================================"
echo ""
echo "Pour lancer l'application :"
echo "  1. Exécutez : ./start_app.sh"
echo "  OU"
echo "  2. Exécutez : source venv/bin/activate && streamlit run app.py"
echo ""
echo "L'application s'ouvrira dans votre navigateur par défaut"
echo ""
