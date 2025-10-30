# Analyseur de Psychologie des Titres YouTube

Projet Scrapy complet pour extraire et analyser la "psychologie" des titres de videos tendances YouTube du monde entier. Le projet utilise BeautifulSoup pour le parsing HTML, spaCy pour l'analyse NLP, et MongoDB Atlas pour le stockage des donnees.

## Fonctionnalites

- Scraping des tendances YouTube mondiales depuis `https://youtube.trends24.in/`
- Extraction des metadonnees : titre, URL, canal, vues, heure, pays
- Analyse psychologique des titres avec calcul de features :
  - Longueur (caracteres et mots)
  - Nombre de majuscules, emojis, chiffres
  - Nombre de points d'interrogation et d'exclamation
  - Ratio de majuscules
  - Nombre de hashtags
  - Langue detectee (FR/EN/AUTRE)
  - Tonalite moyenne via spaCy
  - Score psychologique global
- Stockage dans MongoDB Atlas avec gestion des doublons (mise a jour automatique)
- Export JSON des resultats
- Interface CLI pour visualiser le top des titres les plus accrocheurs

## Structure du Projet

```
Projet/
├── scrapy.cfg                          # Configuration Scrapy
├── requirements.txt                    # Dependances Python
├── README.md                          # Documentation
├── app.py                             # Point d'entree principal
├── utiles.py                          # Classes utilitaires (TextFeatures, MongoClientWrapper)
└── yt_title_psychology/
    ├── __init__.py
    ├── items.py                       # Definition des Items Scrapy
    ├── pipelines.py                   # Pipelines de traitement et stockage
    ├── settings.py                    # Configuration Scrapy
    └── spiders/
        ├── __init__.py
        └── youtube_trends.py          # Spider principal
```

## Installation

### 1. Prerequis

- Python 3.10 ou superieur
- pip (gestionnaire de paquets Python)
- Compte MongoDB Atlas (gratuit)

### 2. Installation des dependances

```bash
# Cloner ou telecharger le projet
cd Projet

# Installer les dependances Python
pip install -r requirements.txt

# Installer le modele francais de spaCy
python -m spacy download fr_core_news_sm
```

### 3. Configuration MongoDB

Le projet est configure pour utiliser MongoDB Atlas. L'URI de connexion est definie dans `yt_title_psychology/settings.py` :

```python
MONGO_URI = "mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster"
MONGO_DATABASE = "youtube"
MONGO_COLLECTION = "youtube"
```

**Note de securite** : Pour la production, utilisez des variables d'environnement pour stocker les credentials MongoDB.

## Utilisation

### Methode 1 : Interface CLI (Recommandee)

Lancez le programme principal avec menu interactif :

```bash
python app.py
```

Options disponibles :
1. Lancer le spider et scraper les tendances
2. Afficher le top 5 des titres les plus accrocheurs
3. Les deux (scraping puis affichage)
4. Quitter

### Methode 2 : Ligne de commande Scrapy

Lancer le spider directement avec Scrapy :

```bash
# Scraping avec export JSON
scrapy crawl youtube_trends -o trending_fr.json

# Scraping sans export (stockage MongoDB uniquement)
scrapy crawl youtube_trends
```

### Methode 3 : Script Python personnalise

```python
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from yt_title_psychology.spiders.youtube_trends import YouTubeTrendsSpider

# Configuration
settings = get_project_settings()

# Lancement du spider
process = CrawlerProcess(settings)
process.crawl(YouTubeTrendsSpider)
process.start()
```

## Features Psychologiques Analysees

### 1. Caracteristiques de base
- **longueur_caracteres** : Nombre total de caracteres du titre
- **longueur_mots** : Nombre de mots dans le titre
- **nb_majuscules** : Nombre de lettres en majuscules
- **ratio_majuscules** : Pourcentage de lettres en majuscules

### 2. Ponctuation et symboles
- **nb_interrogations** : Nombre de points d'interrogation (?)
- **nb_exclamations** : Nombre de points d'exclamation (!)
- **nb_hashtags** : Nombre de hashtags (#)
- **nb_chiffres** : Nombre de chiffres dans le titre

### 3. Elements visuels
- **nb_emojis** : Nombre d'emojis utilises

### 4. Analyse linguistique
- **langue_detectee** : Langue predominante (FR/EN/AUTRE)
- **tonalite_moyenne** : Score de tonalite base sur l'analyse POS de spaCy (0-1)

### 5. Score global
- **score_psychologique** : Score composite (0-100) indiquant le caractere "accrocheur" du titre

### Interpretation du Score Psychologique

Le score psychologique est calcule selon la formule suivante :
- +5 points par point d'exclamation
- +3 points par point d'interrogation
- +4 points par emoji
- Jusqu'a +15 points pour le ratio de majuscules
- Jusqu'a +10 points pour les chiffres
- +10 points si la longueur est optimale (30-60 caracteres)
- Jusqu'a +15 points pour la tonalite emotionnelle
- Jusqu'a +10 points pour les hashtags

**Score maximal : 100 points**

## Gestion des Doublons

Le pipeline MongoDB utilise l'URL de la video comme cle unique. Si une video existe deja dans la base de donnees :
- Les donnees sont **mises a jour** (upsert)
- La `date_scraping` est actualisee
- Les nouvelles features remplacent les anciennes

Cela permet de suivre l'evolution des metriques (vues, position dans les tendances) au fil du temps.

## Architecture Technique

### Spider (youtube_trends.py)

1. **Decouverte des pays** : Parse la page principale pour identifier tous les pays disponibles
2. **Scraping par pays** : Pour chaque pays, extrait les videos tendances
3. **Extraction des donnees** : Utilise BeautifulSoup pour parser le HTML et extraire :
   - Titre (texte du lien ou attribut title)
   - URL (nettoyee pour ne garder que l'ID de video)
   - Canal (recherche dans les elements parents)
   - Vues (parsing de patterns comme "1.2M views")
   - Heure (extraction de patterns temporels)
4. **Calcul des features** : Appel a TextFeatures pour l'analyse NLP
5. **Yield des items** : Envoi au pipeline pour validation et stockage

### Pipeline de Traitement

#### YoutubeTrendsPipeline (Priorite 300)
- Valide la presence des champs obligatoires (titre, URL)
- Attribue des valeurs par defaut aux champs optionnels
- Rejette les items invalides

#### MongoDBPipeline (Priorite 400)
- Etablit la connexion a MongoDB Atlas
- Calcule le score psychologique
- Insere ou met a jour les documents (upsert sur l'URL)
- Gere les erreurs et affiche les statistiques

### Classes Utilitaires (utiles.py)

#### TextFeatures
- `nettoyer_texte()` : Normalisation Unicode et suppression de caracteres de controle
- `compter_emojis()` : Detection des emojis via regex Unicode
- `detecter_langue()` : Detection simple FR/EN base sur des mots courants
- `calculer_tonalite()` : Analyse morphosyntaxique avec spaCy
- `extraire_features()` : Extraction complete de toutes les features
- `calculer_score_psychologique()` : Calcul du score composite

#### MongoClientWrapper
- `connect()` : Etablissement de la connexion MongoDB Atlas
- `insert_or_update()` : Upsert des documents
- `close()` : Fermeture propre de la connexion

## Configuration

### Parametres de Politesse (settings.py)

```python
USER_AGENT = "Mozilla/5.0 ... YoutubeTrendAnalyzer/1.0"
DOWNLOAD_DELAY = 1.5  # 1.5 secondes entre chaque requete
CONCURRENT_REQUESTS = 4
AUTOTHROTTLE_ENABLED = True
```

Ces parametres assurent un scraping respectueux du serveur cible.

### Parametres MongoDB (settings.py)

```python
MONGO_URI = "mongodb+srv://..."
MONGO_DATABASE = "youtube"
MONGO_COLLECTION = "youtube"
```

## Limites et Considerations

### Limites Techniques

1. **Structure HTML dynamique** : Le site trends24.in peut modifier sa structure HTML, necessitant une mise a jour des selecteurs
2. **JavaScript** : Si le site charge le contenu dynamiquement via JavaScript, Scrapy seul ne suffira pas (envisager Selenium ou Scrapy-Splash)
3. **Rate limiting** : Le site peut limiter le nombre de requetes par IP
4. **Donnees incompletes** : Certaines videos peuvent manquer de metadonnees (vues, canal)

### Limites d'Analyse

1. **Detection de langue** : Methode simple basee sur des mots courants, peut etre imprecise pour des titres courts
2. **Tonalite** : Analyse basique via POS tagging, ne capture pas toutes les nuances emotionnelles
3. **Score psychologique** : Formule heuristique basee sur des hypotheses, non validee scientifiquement

### Considerations Ethiques et Legales

1. **Respect du robots.txt** : Verifiez les politiques de scraping du site
2. **Frequence de scraping** : N'executez pas le spider trop frequemment (recommande : 1-2 fois par jour maximum)
3. **Usage des donnees** : A usage educatif et de recherche uniquement
4. **Propriete intellectuelle** : Les titres et metadonnees appartiennent aux createurs de contenu

## Exemples d'Utilisation

### Analyser les tendances d'un pays specifique

Modifiez le spider pour cibler un pays specifique :

```python
# Dans youtube_trends.py, ligne start_urls
start_urls = ['https://youtube.trends24.in/france/']
```

### Exporter vers CSV

Ajoutez l'option `-o` avec l'extension .csv :

```bash
scrapy crawl youtube_trends -o tendances.csv
```

### Planifier l'execution quotidienne (Windows)

Utilisez le Planificateur de taches Windows ou un script PowerShell :

```powershell
# Script execute_spider.ps1
cd C:\Users\Y.chehboub\Downloads\Projet
python app.py
```

### Analyser l'evolution temporelle

Requete MongoDB pour voir l'evolution d'une video :

```javascript
db.youtube.find(
  {url: "https://www.youtube.com/watch?v=VIDEO_ID"},
  {date_scraping: 1, vues: 1, score_psychologique: 1}
).sort({date_scraping: 1})
```

## Troubleshooting

### Erreur : "Module spacy not found"

```bash
pip install spacy
python -m spacy download fr_core_news_sm
```

### Erreur : "Connection to MongoDB failed"

Verifiez :
1. L'URI MongoDB dans settings.py
2. Votre connexion Internet
3. Les credentials MongoDB
4. Les regles de firewall (whitelist IP sur MongoDB Atlas)

### Aucune video scrapee

1. Verifiez la structure HTML du site (peut avoir change)
2. Testez manuellement l'URL dans un navigateur
3. Activez le mode DEBUG dans settings.py : `LOG_LEVEL = "DEBUG"`
4. Verifiez les selecteurs BeautifulSoup dans le spider

### Score psychologique toujours a 0

Verifiez que spaCy est correctement installe et que le modele fr_core_news_sm est disponible :

```bash
python -c "import spacy; nlp = spacy.load('fr_core_news_sm'); print('OK')"
```

## Ameliorations Possibles

### Court terme
- Ajouter Scrapy-Splash pour le rendu JavaScript
- Implementer des tests unitaires (pytest)
- Ajouter un systeme de logging vers fichier
- Creer un dashboard Streamlit pour visualiser les donnees

### Moyen terme
- Utiliser un modele de detection de langue plus robuste (langdetect, fasttext)
- Implementer une analyse de sentiment plus sophistiquee (transformers, CamemBERT)
- Ajouter des metriques d'engagement (likes, commentaires) via l'API YouTube officielle
- Creer un systeme de notification pour les titres tres accrocheurs

### Long terme
- Entrainer un modele de prediction du succes d'une video base sur son titre
- Analyser les tendances temporelles et saisonnieres
- Comparer les strategies de titres entre pays et categories
- Creer un generateur de titres optimises

## Contributions

Ce projet est a usage educatif. Pour toute suggestion ou amelioration :
1. Fork le projet
2. Creez une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -am 'Ajout amelioration'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## Licence

Ce projet est a usage educatif et de recherche uniquement. Respectez les conditions d'utilisation des sites scraped et les droits d'auteur des contenus analyses.

## Auteur

Projet developpe dans le cadre d'un exercice d'ingenierie des donnees et de scraping web.

## Support

Pour toute question ou probleme :
1. Consultez la section Troubleshooting
2. Verifiez les logs Scrapy
3. Testez les connexions (MongoDB, reseau)

---

**Bon scraping et bonne analyse !**
