# Script PowerShell pour le projet YouTube Title Psychology
# Utilisation: .\run.ps1 <commande>

$PYTHON = "C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe"
$OUTPUT = "tendances_youtube.json"

function Show-Help {
    Write-Host "===================================================================" -ForegroundColor Cyan
    Write-Host "       YouTube Title Psychology - Commandes disponibles" -ForegroundColor Cyan
    Write-Host "===================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .\run.ps1 install       - Installer toutes les dependances" -ForegroundColor Green
    Write-Host "  .\run.ps1 test          - Tester l'installation" -ForegroundColor Green
    Write-Host "  .\run.ps1 scrape        - Scraper toutes les tendances YouTube" -ForegroundColor Green
    Write-Host "  .\run.ps1 scrape-quick  - Scraper rapidement (3 pages)" -ForegroundColor Green
    Write-Host "  .\run.ps1 analyze       - Analyser les resultats" -ForegroundColor Green
    Write-Host "  .\run.ps1 run           - Scraper + Analyser (workflow complet)" -ForegroundColor Green
    Write-Host "  .\run.ps1 web           - Lancer l'interface web (Flask)" -ForegroundColor Green
    Write-Host "  .\run.ps1 clean         - Nettoyer les fichiers generes" -ForegroundColor Green
    Write-Host ""
    Write-Host "===================================================================" -ForegroundColor Cyan
}

function Install-Dependencies {
    Write-Host "Installation des dependances Python..." -ForegroundColor Yellow
    & $PYTHON -m pip install --upgrade pip
    & $PYTHON -m pip install scrapy beautifulsoup4 lxml pymongo python-dateutil
    Write-Host "Installation terminee !" -ForegroundColor Green
}

function Test-Installation {
    Write-Host "Test de l'installation..." -ForegroundColor Yellow
    & $PYTHON test_installation.py
}

function Start-Scraping {
    Write-Host "Demarrage du scraping complet..." -ForegroundColor Yellow
    & $PYTHON -m scrapy crawl youtube_trends -o $OUTPUT
    Write-Host "Scraping termine ! Resultats dans $OUTPUT" -ForegroundColor Green
}

function Start-QuickScraping {
    Write-Host "Demarrage du scraping rapide (3 pages)..." -ForegroundColor Yellow
    & $PYTHON -m scrapy crawl youtube_trends -o $OUTPUT -s CLOSESPIDER_PAGECOUNT=3
    Write-Host "Scraping rapide termine ! Resultats dans $OUTPUT" -ForegroundColor Green
}

function Start-Analysis {
    Write-Host "Analyse des resultats..." -ForegroundColor Yellow
    & $PYTHON scripts\\analyser_resultats.py $OUTPUT
}

function Start-FullWorkflow {
    Write-Host "Demarrage du workflow complet..." -ForegroundColor Yellow
    Start-Scraping
    Start-Analysis
    Write-Host "Workflow complet termine !" -ForegroundColor Green
}

function Start-QuickWorkflow {
    Write-Host "Demarrage du workflow rapide..." -ForegroundColor Yellow
    Start-QuickScraping
    Start-Analysis
    Write-Host "Workflow rapide termine !" -ForegroundColor Green
}

function Clear-GeneratedFiles {
    Write-Host "Nettoyage des fichiers..." -ForegroundColor Yellow
    Remove-Item *.json -ErrorAction SilentlyContinue
    Remove-Item *.csv -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .scrapy -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force httpcache -ErrorAction SilentlyContinue
    Write-Host "Nettoyage termine !" -ForegroundColor Green
}

function Start-App {
    Write-Host "Demarrage de l'interface CLI..." -ForegroundColor Yellow
    & $PYTHON app.py
}

function Start-WebApp {
    Write-Host "Demarrage de l'application web..." -ForegroundColor Yellow
    Write-Host "Ouvrez votre navigateur sur: http://localhost:5000" -ForegroundColor Green
    # Enable MongoDB now that connection is working
    $env:USE_MONGODB = "true"
    & $PYTHON dashboard\\web_app.py
}

function Show-Version {
    Write-Host "Versions des packages:" -ForegroundColor Yellow
    & $PYTHON -c "import scrapy, bs4, pymongo; print('Scrapy:', scrapy.__version__); print('BeautifulSoup:', bs4.__version__); print('PyMongo:', pymongo.__version__)"
}

function Show-Count {
    Write-Host "Nombre de videos scrapees:" -ForegroundColor Yellow
    & $PYTHON -c "import json; data=json.load(open('$OUTPUT', 'r', encoding='utf-8')); print(len(data), 'videos')"
}

# Traitement de la commande
$command = $args[0]

switch ($command) {
    "install" { Install-Dependencies }
    "test" { Test-Installation }
    "scrape" { Start-Scraping }
    "scrape-quick" { Start-QuickScraping }
    "analyze" { Start-Analysis }
    "run" { Start-FullWorkflow }
    "run-quick" { Start-QuickWorkflow }
    "web" { Start-WebApp }
    "clean" { Clear-GeneratedFiles }
    
    "version" { Show-Version }
    "count" { Show-Count }
    default { Show-Help }
}
