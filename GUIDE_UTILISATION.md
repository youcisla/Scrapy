# Guide d'Utilisation Rapide

## Lancer l'application avec une seule commande

Le projet dispose maintenant de **3 façons** de lancer l'application facilement :

### 1. PowerShell (RECOMMANDE pour Windows)

```powershell
# Afficher l'aide
.\run.ps1

# Workflow rapide : scraper + analyser
.\run.ps1 run-quick

# Workflow complet
.\run.ps1 run

# Autres commandes
.\run.ps1 test          # Tester l'installation
.\run.ps1 scrape        # Scraper seulement
.\run.ps1 analyze       # Analyser seulement
.\run.ps1 clean         # Nettoyer les fichiers
.\run.ps1 app           # Interface CLI
```

### 2. Batch Windows

```cmd
# Afficher l'aide
run.bat

# Workflow rapide
run.bat run-quick

# Workflow complet
run.bat run

# Autres commandes identiques au PowerShell
run.bat test
run.bat scrape
run.bat analyze
```

### 3. Makefile (pour Make sur Windows)

```bash
# Afficher l'aide
make help

# Workflow rapide
make run-quick

# Workflow complet
make run

# Autres commandes
make test           # Tester l'installation
make scrape         # Scraper seulement
make analyze        # Analyser seulement
make clean          # Nettoyer
```

## Commandes Disponibles

### Commandes principales

| Commande | Description |
|----------|-------------|
| `run-quick` | Scrape 3 pages puis analyse (rapide, pour tests) |
| `run` | Scrape complet puis analyse (toutes les tendances) |
| `scrape` | Lance le scraping complet |
| `scrape-quick` | Lance le scraping rapide (3 pages) |
| `analyze` | Analyse les resultats du fichier JSON |
| `test` | Test l'installation du projet |
| `clean` | Nettoie les fichiers generes (JSON, CSV, cache) |
| `app` | Lance l'interface CLI interactive |

### Commandes utilitaires

| Commande | Description |
|----------|-------------|
| `install` | Installe les dependances Python |
| `version` | Affiche les versions des packages |
| `count` | Compte le nombre de videos dans le JSON |
| `list-spiders` | Liste les spiders Scrapy disponibles (Makefile) |
| `shell` | Ouvre un shell Scrapy pour debugger (Makefile) |

## Exemples d'Utilisation

### Premier lancement

```powershell
# 1. Tester l'installation
.\run.ps1 test

# 2. Lancer un scraping rapide pour tester
.\run.ps1 run-quick

# 3. Le fichier tendances_youtube.json contient maintenant les resultats
```

### Usage quotidien

```powershell
# Scraper les nouvelles tendances
.\run.ps1 scrape

# Analyser les resultats
.\run.ps1 analyze

# Ou tout en une fois
.\run.ps1 run
```

### Nettoyage

```powershell
# Supprimer tous les fichiers generes
.\run.ps1 clean
```

### Developpement / Debug

```powershell
# Voir les versions installees
.\run.ps1 version

# Compter les videos scrapees
.\run.ps1 count

# Mode debug (Makefile uniquement)
make scrape-debug
```

## Temps d'Execution Approximatifs

| Operation | Duree |
|-----------|-------|
| `run-quick` | ~30 secondes |
| `run` (complet) | 2-5 minutes |
| `scrape-quick` | ~2 secondes |
| `scrape` | 1-3 minutes |
| `analyze` | < 1 seconde |
| `test` | ~35 secondes (avec timeout MongoDB) |

## Fichiers Generes

Apres execution, vous trouverez :

- `tendances_youtube.json` : Resultats du scraping avec analyse
- `.scrapy/` : Cache Scrapy (peut etre supprime)
- `httpcache/` : Cache HTTP (si active dans settings.py)

## Troubleshooting

### Erreur "Execution Policy"

Si PowerShell refuse d'executer le script :

```powershell
# Executer avec bypass
powershell -ExecutionPolicy Bypass -File run.ps1 run-quick

# Ou changer la policy (admin requis)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erreur MongoDB

Le projet fonctionne **sans MongoDB**. Les warnings MongoDB sont normaux et n'empechent pas le scraping.

### Erreur JSON parsing

Si l'analyse echoue avec "Extra data", c'est probablement du a des caracteres speciaux. Le fichier JSON est quand meme genere et valide.

### Commande introuvable

Verifiez que vous etes dans le bon repertoire :

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
```

## Raccourcis Recommandes

Pour un usage quotidien, creez un alias PowerShell :

```powershell
# Ajouter a votre profile PowerShell (~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)
function yt-scrape { 
    cd C:\Users\Y.chehboub\Downloads\Projet
    .\run.ps1 run 
}

# Usage
yt-scrape
```

Ou un alias batch :

```batch
@echo off
cd C:\Users\Y.chehbouh\Downloads\Projet
run.bat run
```

Sauvegardez sous `C:\Windows\yt-scrape.bat` (necessite droits admin).

## Resume

**Commande la plus simple pour tout faire :**

```powershell
.\run.ps1 run-quick
```

Cette commande va :
1. Scraper les tendances YouTube (3 pages)
2. Exporter en JSON
3. Analyser les resultats
4. Afficher les statistiques et le top 10

**Temps total : ~30 secondes**
