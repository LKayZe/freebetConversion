# 🚀 Guide de Déploiement : Streamlit Cloud

Votre application est prête à être déployée gratuitement sur **Streamlit Community Cloud**.

## 1. Prérequis (Déjà fait ✅)
- [x] **Code propre** : Les fichiers inutiles ont été supprimés.
- [x] **requirements.txt** : Liste des librairies Python (`selenium`, `bs4`, etc.).
- [x] **packages.txt** : Liste des paquets système pour le Cloud (`chromium`).
- [x] **Configuration Headless** : Le scraper Betclic est configuré pour tourner sans écran.

## 2. Pousser le code sur GitHub
Streamlit Cloud se connecte directement à votre compte GitHub.
1. Créez un **Nouveau Répository** sur [GitHub.com](https://github.com/new).
2. Uploadez tous les fichiers du dossier `scrapW` dans ce repository (ou utilisez git en ligne de commande).

## 3. Déployer sur Streamlit Cloud
1. Allez sur [share.streamlit.io](https://share.streamlit.io/).
2. Connectez-vous avec votre compte GitHub.
3. Cliquez sur **"New app"**.
4. Sélectionnez votre repository et la branche (ex: `main`).
5. Indiquez le **Main file path** : `app.py`.
6. Cliquez sur **Deploy**.

## ⚠️ Limitations Connues (Cloud)
- **Scraping Selenium (Betclic Early Win)** : Le cloud Streamlit est sous Linux. Bien que nous ayons ajouté `packages.txt` et configuré le mode headless, le scraping Selenium est parfois instable ou lent sur les serveurs gratuits (taux de succès variable).
- **Scraping HTTP (Winamax / PSEL)** : Fonctionnera parfaitement et rapidement.

## 💡 Astuce
Si le déploiement échoue ou si Selenium bloque, vous pouvez toujours lancer l'app **en local** avec le fichier `run_app.bat`.
