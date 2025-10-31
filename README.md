# Analyseur de Psychologie des Titres YouTube

Projet Scrapy pour extraire et analyser les caractéristiques psychologiques des titres de vidéos tendances YouTube à travers le monde.

## Fonctionnalités

- Scrape les vidéos tendances YouTube depuis `https://youtube.trends24.in/`
- Extrait les métadonnées : titre, URL, chaîne, vues, pays
- Analyse les caractéristiques psychologiques : longueur, emojis, ponctuation, ratio de majuscules, mots clickbait
- Calcule un score psychologique (0-100) basé sur une formule pondérée
- Stocke dans MongoDB Atlas avec gestion des doublons (upsert par URL)
- Interface web pour visualiser les données

## Installation

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
```

## Utilisation

```powershell
# Démarrer le tableau de bord web
.\run.ps1 web

# Lancer le scraper
.\run.ps1 scrape
```

## Calcul du Score Psychologique

**Formule** : `Score = Σ(Caractéristique_normalisée × Poids) × 100`

**Composants** :
- Longueur du titre (25%)
- Points d'exclamation (20%)
- Points d'interrogation (15%)
- Lettres majuscules (20%)
- Mots clickbait (10%)
- Emojis (10%)

**Exemple** : "INCROYABLE! Comment Gagner 1000€ en 24h? 🔥" → Score : 41.2/100

## Configuration MongoDB

Modifier `yt_title_psychology/settings.py` :

```python
MONGO_URI = "mongodb+srv://..."
MONGO_DATABASE = "youtube"
MONGO_COLLECTION = "youtube"
```

## Gestion des Doublons

Les vidéos sont identifiées de manière unique par leur URL. Lors d'une nouvelle extraction :
- Les vidéos existantes sont **mises à jour** (opération upsert)
- Les nouvelles vidéos sont **insérées**
- Le champ URL dispose d'un index unique pour les performances
