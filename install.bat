@echo off
echo ========================================
echo Installation de Freebet Optimizer
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://www.python.org/downloads/
    echo N'oubliez pas de cocher "Add Python to PATH" lors de l'installation
    pause
    exit /b 1
)

echo [OK] Python est installé
python --version
echo.

REM Vérifier si pip est installé
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] pip n'est pas installé
    echo Installation de pip...
    python -m ensurepip --upgrade
)

echo [OK] pip est installé
echo.

REM Créer un environnement virtuel (optionnel mais recommandé)
echo Creation de l'environnement virtuel...
if not exist "venv" (
    python -m venv venv
    echo [OK] Environnement virtuel créé
) else (
    echo [INFO] Environnement virtuel déjà existant
)
echo.

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

REM Mettre à jour pip
echo Mise à jour de pip...
python -m pip install --upgrade pip
echo.

REM Installer les dépendances
echo Installation des dépendances Python...
pip install -r requirements.txt
echo.

REM Vérifier l'installation de Chrome/Chromium
echo ========================================
echo Vérification de Chrome/Chromium
echo ========================================
echo.
echo [INFO] Selenium nécessite Chrome ou Chromium pour fonctionner
echo [INFO] Le webdriver sera téléchargé automatiquement au premier lancement
echo.

REM Créer un fichier de lancement rapide
echo Creation du fichier de lancement...
(
echo @echo off
echo call venv\Scripts\activate.bat
echo streamlit run app.py
echo pause
) > start_app.bat
echo [OK] Fichier start_app.bat créé
echo.

echo ========================================
echo Installation terminée avec succès !
echo ========================================
echo.
echo Pour lancer l'application :
echo   1. Double-cliquez sur start_app.bat
echo   OU
echo   2. Exécutez : streamlit run app.py
echo.
echo L'application s'ouvrira dans votre navigateur par défaut
echo.
pause
