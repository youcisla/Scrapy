# Guide d'Installation et de Demarrage Rapide

## Installation pas a pas

### Etape 1 : Installer les dependances

```powershell
# Dans le repertoire du projet
cd C:\Users\Y.chehboub\Downloads\Projet

# Installer les packages Python
pip install -r requirements.txt

# Installer le modele francais de spaCy
python -m spacy download fr_core_news_sm
```

### Etape 2 : Verifier l'installation

```powershell
# Verifier que Scrapy est installe
scrapy version

# Verifier que spaCy fonctionne
python -c "import spacy; nlp = spacy.load('fr_core_news_sm'); print('spaCy OK')"

# Verifier la connexion MongoDB
python -c "from pymongo import MongoClient; from pymongo.server_api import ServerApi; client = MongoClient('mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster', server_api=ServerApi('1')); client.admin.command('ping'); print('MongoDB OK')"
```

### Etape 3 : Lancer le projet

#### Methode A : Interface CLI (Recommandee)

```powershell
python app.py
```

Puis choisissez l'option 3 pour scraper et afficher les resultats.

#### Methode B : Ligne de commande Scrapy

```powershell
# Scraping avec export JSON
scrapy crawl youtube_trends -o trending_fr.json

# Puis afficher les resultats
python -c "from app import afficher_top_titres; afficher_top_titres('mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster')"
```

## Commandes Utiles

### Scraping

```powershell
# Scraping standard avec export JSON
scrapy crawl youtube_trends -o tendances.json

# Scraping avec export CSV
scrapy crawl youtube_trends -o tendances.csv

# Scraping sans export (MongoDB uniquement)
scrapy crawl youtube_trends

# Mode debug pour voir tous les details
scrapy crawl youtube_trends -L DEBUG
```

### Gestion MongoDB

```powershell
# Se connecter a MongoDB et afficher les stats
python -c "
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = 'mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster'
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['youtube']
collection = db['youtube']

print(f'Nombre de videos : {collection.count_documents({})}')
print(f'Pays : {collection.distinct(\"pays\")}')
"
```

## Structure Finale du Projet

```
Projet/
├── scrapy.cfg                              # Config Scrapy
├── requirements.txt                        # Dependances
├── README.md                              # Documentation complete
├── INSTALLATION.md                        # Ce guide
├── app.py                                 # Point d'entree
├── utiles.py                              # Utilitaires NLP et MongoDB
└── yt_title_psychology/
    ├── __init__.py
    ├── items.py                           # Definition des Items
    ├── pipelines.py                       # Pipelines de traitement
    ├── settings.py                        # Configuration
    └── spiders/
        ├── __init__.py
        └── youtube_trends.py              # Spider principal
```

## Troubleshooting Rapide

### Probleme : Erreur d'import spacy

**Solution :**
```powershell
pip install --upgrade spacy
python -m spacy download fr_core_news_sm
```

### Probleme : Scrapy non trouve

**Solution :**
```powershell
pip install --upgrade scrapy
```

### Probleme : Connexion MongoDB echouee

**Verifications :**
1. Connexion Internet active
2. URI MongoDB correcte dans settings.py
3. IP autorisee sur MongoDB Atlas (0.0.0.0/0 pour tout autoriser)

### Probleme : Aucune video scrapee

**Solutions :**
1. Verifier que le site est accessible : `https://youtube.trends24.in/`
2. Lancer en mode DEBUG : `scrapy crawl youtube_trends -L DEBUG`
3. Verifier la structure HTML du site (peut avoir change)

## Tests Rapides

### Test 1 : Extraction de features

```powershell
python -c "
from utiles import TextFeatures

tf = TextFeatures()
features = tf.extraire_features('INCROYABLE ! Cette video va vous surprendre')
print(features)
print(f'Score : {tf.calculer_score_psychologique(features)}')
"
```

### Test 2 : Connexion MongoDB

```powershell
python -c "
from utiles import MongoClientWrapper

mongo = MongoClientWrapper(
    uri='mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster',
    db_name='youtube',
    collection_name='youtube'
)
mongo.connect()
print('Connexion OK')
mongo.close()
"
```

### Test 3 : Spider (dry-run)

```powershell
scrapy crawl youtube_trends --nolog -s CLOSESPIDER_PAGECOUNT=1
```

## Prochaines Etapes

1. Executer le spider pour la premiere fois
2. Verifier les donnees dans MongoDB
3. Analyser les resultats
4. Planifier des executions regulieres (optionnel)

Consultez le README.md pour plus de details sur l'utilisation avancee.
