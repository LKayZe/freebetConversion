# 📦 Guide d'Installation - Freebet Optimizer

Ce guide vous explique comment installer et lancer l'application Freebet Optimizer sur votre système.

## 📋 Prérequis

- **Python 3.8 ou supérieur** ([Télécharger Python](https://www.python.org/downloads/))
- **Chrome ou Chromium** (pour le scraping Selenium)
- **Connexion Internet** (pour le scraping des bookmakers)

---

## 🪟 Installation sur Windows

### Méthode automatique (recommandée)

1. **Téléchargez le projet** ou clonez-le avec Git :
   ```bash
   git clone <url-du-repo>
   cd freebetConversion
   ```

2. **Double-cliquez sur `install.bat`**
   - Le script va :
     - Vérifier Python et pip
     - Créer un environnement virtuel
     - Installer toutes les dépendances
     - Créer un fichier de lancement `start_app.bat`

3. **Lancez l'application** en double-cliquant sur `start_app.bat`

### Méthode manuelle

```cmd
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
venv\Scripts\activate.bat

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

---

## 🐧 Installation sur Linux

### Méthode automatique (recommandée)

1. **Téléchargez le projet** :
   ```bash
   git clone <url-du-repo>
   cd freebetConversion
   ```

2. **Rendez le script exécutable et lancez-le** :
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Lancez l'application** :
   ```bash
   ./start_app.sh
   ```

### Méthode manuelle

```bash
# Installer Python et pip (si nécessaire)
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Installer Chrome/Chromium
sudo apt-get install chromium-browser chromium-chromedriver

# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

---

## 🍎 Installation sur macOS

### Méthode automatique (recommandée)

1. **Téléchargez le projet** :
   ```bash
   git clone <url-du-repo>
   cd freebetConversion
   ```

2. **Rendez le script exécutable et lancez-le** :
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Lancez l'application** :
   ```bash
   ./start_app.sh
   ```

### Méthode manuelle

```bash
# Installer Homebrew (si nécessaire)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python
brew install python3

# Installer Chrome
brew install --cask google-chrome

# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

---

## 🚀 Utilisation

Une fois l'installation terminée :

1. **Lancez l'application** :
   - Windows : Double-cliquez sur `start_app.bat`
   - Linux/macOS : Exécutez `./start_app.sh`

2. **L'application s'ouvre automatiquement** dans votre navigateur par défaut à l'adresse `http://localhost:8501`

3. **Configurez vos paramètres** dans la barre latérale :
   - Choisissez votre bookmaker (Betclic, Winamax, PSEL)
   - Définissez votre gain net visé
   - Sélectionnez le nombre de matchs à analyser
   - Cliquez sur "Lancer l'analyse"

---

## 📦 Dépendances installées

Le projet installe automatiquement les packages suivants :

- **streamlit** - Framework web pour l'interface
- **requests** - Requêtes HTTP
- **beautifulsoup4** - Parsing HTML
- **selenium** - Automatisation du navigateur
- **webdriver-manager** - Gestion automatique des drivers Chrome
- **pandas** - Manipulation de données
- **jinja2** - Moteur de templates (pour le styling)
- **cloudscraper** - Contournement Cloudflare
- **matplotlib** - Graphiques (optionnel)

---

## 🔧 Dépannage

### Erreur : "Python n'est pas reconnu"
- **Solution** : Installez Python et cochez "Add Python to PATH" lors de l'installation
- Ou ajoutez manuellement Python au PATH système

### Erreur : "Chrome/Chromium introuvable"
- **Solution** : Installez Google Chrome ou Chromium
  - Windows : [Télécharger Chrome](https://www.google.com/chrome/)
  - Linux : `sudo apt-get install chromium-browser`
  - macOS : `brew install --cask google-chrome`

### Erreur : "Module not found"
- **Solution** : Réinstallez les dépendances
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```

### L'application ne se lance pas
- **Vérifiez** que l'environnement virtuel est activé
- **Windows** : `venv\Scripts\activate.bat`
- **Linux/macOS** : `source venv/bin/activate`

### Erreur de scraping
- **Vérifiez** votre connexion Internet
- **Attendez** quelques secondes (le scraping peut être lent)
- **Essayez** un autre bookmaker si l'un ne fonctionne pas

---

## 📝 Notes importantes

- **Premier lancement** : Le téléchargement du ChromeDriver peut prendre quelques secondes
- **Cache** : Les données sont mises en cache pendant 10 minutes pour éviter trop de requêtes
- **Selenium** : Le scraping Betclic Early Win utilise Selenium et peut être plus lent
- **Cloudflare** : Certains sites peuvent bloquer les requêtes automatiques

---

## 🆘 Support

Si vous rencontrez des problèmes :

1. Vérifiez que tous les prérequis sont installés
2. Consultez la section Dépannage ci-dessus
3. Vérifiez les logs dans le terminal
4. Assurez-vous d'avoir la dernière version du projet

---

## 📄 Licence

Ce projet est fourni tel quel, sans garantie. Utilisez-le de manière responsable et conformément aux conditions d'utilisation des bookmakers.
