# Guide de Resolution des Problemes d'Installation

## Probleme : Microsoft Visual C++ 14.0 requis pour spaCy

### Symptome
```
error: Microsoft Visual C++ 14.0 or greater is required.
```

### Solution 1 : Utiliser le projet sans spaCy (RECOMMANDE pour debuter)

Le projet fonctionne parfaitement sans spaCy. Les features NLP sont calculees avec des regex :

```powershell
# Les packages de base sont deja installes
# Verifier l'installation
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -c "import scrapy, pymongo, bs4; print('Installation OK')"

# Tester le projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe app.py
```

**Fonctionnalites disponibles sans spaCy :**
- Longueur (caracteres et mots)
- Nombre de majuscules, emojis, chiffres
- Points d'interrogation et exclamation
- Ratio de majuscules
- Hashtags
- Detection de langue simple (FR/EN)
- Tonalite basique (calculee sans spaCy)

### Solution 2 : Installer Visual Studio Build Tools (pour spaCy complet)

1. **Telecharger Build Tools** :
   - Aller sur : https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Telecharger "Build Tools for Visual Studio 2022"

2. **Installer avec les composants C++** :
   - Lancer l'installateur
   - Cocher "Desktop development with C++"
   - Installer (environ 6 GB)

3. **Redemarrer le terminal PowerShell**

4. **Installer spaCy** :
   ```powershell
   C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m pip install spacy
   C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m spacy download fr_core_news_sm
   ```

### Solution 3 : Utiliser des wheels precompilees

Pour Python 3.14, il n'y a pas encore de wheels precompilees pour spaCy. Options :

**Option A : Downgrade vers Python 3.12 (plus stable)**

```powershell
# Creer un nouvel environnement virtuel avec Python 3.12
python3.12 -m venv .venv312
.venv312\Scripts\Activate.ps1
pip install -r requirements.txt
pip install spacy
python -m spacy download fr_core_news_sm
```

**Option B : Attendre une version stable de spaCy pour Python 3.14**

Python 3.14 est tres recent (sorti en octobre 2024). Beaucoup de packages n'ont pas encore de support complet.

## Test de l'Installation

### Test 1 : Packages de base (sans spaCy)

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -c "
import scrapy
import bs4
import pymongo
from utiles import TextFeatures

print('✓ Scrapy:', scrapy.__version__)
print('✓ BeautifulSoup:', bs4.__version__)
print('✓ PyMongo:', pymongo.__version__)

tf = TextFeatures(use_spacy=False)
features = tf.extraire_features('TEST : Ceci est un test !')
print('✓ TextFeatures:', features)
print('✓ Score:', tf.calculer_score_psychologique(features))
"
```

### Test 2 : Connexion MongoDB

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -c "
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = 'mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster'
client = MongoClient(uri, server_api=ServerApi('1'))
client.admin.command('ping')
print('✓ Connexion MongoDB reussie')
client.close()
"
```

### Test 3 : Spider Scrapy

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy list
```

Devrait afficher : `youtube_trends`

## Lancer le Projet (SANS spaCy)

### Methode 1 : Interface CLI

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe app.py
```

### Methode 2 : Scrapy direct

```powershell
cd C:\Users\Y.chehboub\Downloads\Projet
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m scrapy crawl youtube_trends -o resultats.json
```

## Commandes Utiles

### Verifier la version de Python

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe --version
```

### Lister les packages installes

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m pip list
```

### Mettre a jour pip

```powershell
C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe -m pip install --upgrade pip
```

## Recommendations

1. **Pour debuter** : Utilisez le projet sans spaCy (fonctionne parfaitement)
2. **Pour production** : Installez Visual Studio Build Tools puis spaCy
3. **Alternative** : Utilisez Python 3.12 au lieu de 3.14 (plus stable)

## Support

Si vous rencontrez d'autres problemes :

1. Verifiez que vous etes dans le bon repertoire :
   ```powershell
   pwd  # Devrait afficher C:\Users\Y.chehboub\Downloads\Projet
   ```

2. Verifiez l'environnement virtuel :
   ```powershell
   Get-Command python | Select-Object Source
   # Devrait pointer vers .venv\Scripts\python.exe
   ```

3. En cas de doute, recreez l'environnement virtuel :
   ```powershell
   Remove-Item -Recurse -Force .venv
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install scrapy beautifulsoup4 lxml pymongo python-dateutil
   ```
