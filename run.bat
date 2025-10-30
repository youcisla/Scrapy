@echo off
REM Script Batch pour le projet YouTube Title Psychology
REM Utilisation: run.bat <commande>

set PYTHON=C:\Users\Y.chehboub\Downloads\Projet\.venv\Scripts\python.exe
set OUTPUT=tendances_youtube.json

if "%1"=="" goto help
if "%1"=="install" goto install
if "%1"=="test" goto test
if "%1"=="scrape" goto scrape
if "%1"=="scrape-quick" goto scrape-quick
if "%1"=="analyze" goto analyze
if "%1"=="run" goto run
if "%1"=="run-quick" goto run-quick
if "%1"=="clean" goto clean
if "%1"=="app" goto app
if "%1"=="version" goto version
if "%1"=="count" goto count
goto help

:help
echo ===================================================================
echo        YouTube Title Psychology - Commandes disponibles
echo ===================================================================
echo.
echo   run.bat install       - Installer toutes les dependances
echo   run.bat test          - Tester l'installation
echo   run.bat scrape        - Scraper toutes les tendances YouTube
echo   run.bat scrape-quick  - Scraper rapidement (3 pages)
echo   run.bat analyze       - Analyser les resultats
echo   run.bat run           - Scraper + Analyser (workflow complet)
echo   run.bat run-quick     - Scraper rapide + Analyser
echo   run.bat clean         - Nettoyer les fichiers generes
echo   run.bat app           - Lancer l'interface CLI
echo   run.bat version       - Afficher les versions des packages
echo   run.bat count         - Compter les videos scrapees
echo.
echo ===================================================================
goto end

:install
echo Installation des dependances Python...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install scrapy beautifulsoup4 lxml pymongo python-dateutil
echo Installation terminee !
goto end

:test
echo Test de l'installation...
%PYTHON% test_installation.py
goto end

:scrape
echo Demarrage du scraping complet...
%PYTHON% -m scrapy crawl youtube_trends -o %OUTPUT%
echo Scraping termine ! Resultats dans %OUTPUT%
goto end

:scrape-quick
echo Demarrage du scraping rapide (3 pages)...
%PYTHON% -m scrapy crawl youtube_trends -o %OUTPUT% -s CLOSESPIDER_PAGECOUNT=3
echo Scraping rapide termine ! Resultats dans %OUTPUT%
goto end

:analyze
echo Analyse des resultats...
%PYTHON% analyser_resultats.py %OUTPUT%
goto end

:run
echo Demarrage du workflow complet...
call :scrape
call :analyze
echo Workflow complet termine !
goto end

:run-quick
echo Demarrage du workflow rapide...
call :scrape-quick
call :analyze
echo Workflow rapide termine !
goto end

:clean
echo Nettoyage des fichiers...
del /Q *.json 2>nul
del /Q *.csv 2>nul
rmdir /S /Q .scrapy 2>nul
rmdir /S /Q httpcache 2>nul
echo Nettoyage termine !
goto end

:app
echo Demarrage de l'interface CLI...
%PYTHON% app.py
goto end

:version
echo Versions des packages:
%PYTHON% -c "import scrapy, bs4, pymongo; print('Scrapy:', scrapy.__version__); print('BeautifulSoup:', bs4.__version__); print('PyMongo:', pymongo.__version__)"
goto end

:count
echo Nombre de videos scrapees:
%PYTHON% -c "import json; data=json.load(open('%OUTPUT%', 'r', encoding='utf-8')); print(len(data), 'videos')"
goto end

:end
