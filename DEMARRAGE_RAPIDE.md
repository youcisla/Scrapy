# DEMARRAGE RAPIDE

## Le projet est installe et pret !

### Lancer le scraping maintenant

**Option 1 : Export JSON uniquement (RECOMMANDE pour le premier test)**

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy crawl youtube_trends -o tendances_youtube.json
```

Cette commande va :
- Scraper toutes les tendances YouTube mondiales
- Exporter les resultats dans `tendances_youtube.json`
- Pas besoin de MongoDB pour ce test

**Option 2 : Interface CLI complete**

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe app.py
```

## Resoudre le probleme MongoDB

### Etape 1 : Verifier l'IP autorisee

1. Aller sur https://cloud.mongodb.com/
2. Se connecter avec vos credentials
3. Cliquer sur "Network Access" dans le menu gauche
4. Cliquer sur "Add IP Address"
5. Choisir "Allow Access from Anywhere" (0.0.0.0/0)
6. Cliquer sur "Confirm"

### Etape 2 : Re-tester la connexion

```powershell
C:/Users/Y.chehbouh/Downloads/Projet/.venv/Scripts/python.exe test_installation.py
```

### Etape 3 : Si MongoDB est toujours inaccessible

Vous pouvez :
- Utiliser uniquement l'export JSON (fonctionne parfaitement)
- Ou installer MongoDB localement :
  ```powershell
  # Modifier dans settings.py :
  MONGO_URI = "mongodb://localhost:27017/"
  ```

## Commandes Utiles

### Tester l'installation
```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe test_installation.py
```

### Scraper avec limite (pour test rapide)
```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy crawl youtube_trends -o test.json -s CLOSESPIDER_PAGECOUNT=5
```

### Voir les logs en temps reel
```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy crawl youtube_trends -L DEBUG
```

### Lister les spiders disponibles
```powershell
C:/Users/Y.chehbouh/Downloads/Projet/.venv/Scripts/python.exe -m scrapy list
```

## Prochaines Etapes

1. **Premier test** : Lancez un scraping avec export JSON
2. **Analyser les resultats** : Ouvrez `tendances_youtube.json` pour voir les donnees
3. **Resoudre MongoDB** : Suivez les etapes ci-dessus si vous voulez le stockage en base
4. **Installer spaCy** (optionnel) : Voir TROUBLESHOOTING.md pour les instructions

## Besoin d'aide ?

- Tests : `python test_installation.py`
- Documentation complete : `README.md`
- Resolution de problemes : `TROUBLESHOOTING.md`

## Votre premier scraping en une commande

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy crawl youtube_trends -o ma_premiere_analyse.json
```

Attendez quelques minutes... et voila ! Vous aurez un fichier JSON avec toutes les tendances YouTube mondiales analysees.
