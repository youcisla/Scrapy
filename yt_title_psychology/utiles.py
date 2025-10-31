"""
Utilitaires partages pour le projet d analyse des tendances YouTube
"""
import json
import os
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import re

# Safe __file__ fallback
try:
    _current_file = Path(__file__).resolve()
except NameError:
    _current_file = Path(os.getcwd()) / 'yt_title_psychology' / 'utiles.py'


class TextFeatures:
    """Classe pour extraire des features textuelles des titres YouTube"""
    
    def __init__(self, text):
        self.text = text
        self.text_lower = text.lower() if text else ""
    
    def count_caps(self):
        """Compte le nombre de caracteres en majuscules"""
        if not self.text:
            return 0
        return sum(1 for c in self.text if c.isupper())
    
    def count_exclamation(self):
        """Compte le nombre de points d exclamation"""
        if not self.text:
            return 0
        return self.text.count('!')
    
    def count_question(self):
        """Compte le nombre de points d interrogation"""
        if not self.text:
            return 0
        return self.text.count('?')
    
    def has_emoji(self):
        """Detecte la presence d emojis"""
        if not self.text:
            return False
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(self.text))
    
    def has_numbers(self):
        """Detecte la presence de nombres"""
        if not self.text:
            return False
        return bool(re.search(r'\d', self.text))
    
    def word_count(self):
        """Compte le nombre de mots"""
        if not self.text:
            return 0
        return len(self.text.split())
    
    def char_count(self):
        """Compte le nombre de caracteres"""
        if not self.text:
            return 0
        return len(self.text)
    
    def caps_ratio(self):
        """Ratio de caracteres en majuscules"""
        if not self.text:
            return 0.0
        letters = sum(1 for c in self.text if c.isalpha())
        if letters == 0:
            return 0.0
        return self.count_caps() / letters
    
    def has_clickbait_words(self):
        """Detecte des mots clickbait courants"""
        if not self.text_lower:
            return False
        clickbait_words = [
            'incroyable', 'choc', 'revelation', 'secret', 'astuce',
            'amazing', 'shocking', 'unbelievable', 'must see', 'epic', 'insane', 'crazy', 'best', 'worst'
        ]
        return any(word in self.text_lower for word in clickbait_words)
    
    def count_emojis(self):
        """Compte le nombre d'emojis dans le texte"""
        if not self.text:
            return 0
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        matches = emoji_pattern.findall(self.text)
        return sum(len(match) for match in matches)
    
    def count_hashtags(self):
        """Compte le nombre de hashtags dans le texte"""
        if not self.text:
            return 0
        hashtag_pattern = re.compile(r'#\w+')
        return len(hashtag_pattern.findall(self.text))
    
    def get_all_features(self):
        """Retourne un dictionnaire avec toutes les features"""
        return {
            'caps_count': self.count_caps(),
            'exclamation_count': self.count_exclamation(),
            'question_count': self.count_question(),
            'has_emoji': self.has_emoji(),
            'has_numbers': self.has_numbers(),
            'word_count': self.word_count(),
            'char_count': self.char_count(),
            'caps_ratio': self.caps_ratio(),
            'has_clickbait_words': self.has_clickbait_words(),
            'longueur': self.char_count(),
            'nb_emojis': self.count_emojis(),
            'nb_hashtags': self.count_hashtags(),
            'nb_exclamations': self.count_exclamation(),
            'nb_questions': self.count_question(),
            'pourcentage_majuscules': round(self.caps_ratio() * 100, 2)
        }


class MongoClientWrapper:
    """Wrapper pour gerer la connexion MongoDB"""
    
    def __init__(self, uri, database_name, collection_name, timeout_ms=5000):
        """
        Initialise le wrapper MongoDB
        
        Args:
            uri: URI de connexion MongoDB
            database_name: Nom de la base de donnees
            collection_name: Nom de la collection
            timeout_ms: Timeout en millisecondes pour la connexion
        """
        self.uri = uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.timeout_ms = timeout_ms
        self.client = None
        self.db = None
        self.collection = None
        self._connected = False
    
    def connect(self):
        """Etablit la connexion a MongoDB"""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout_ms
            )
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            self._connected = True
            print(f"Connexion MongoDB etablie: {self.database_name}.{self.collection_name}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self._connected = False
            print(f"Echec de connexion MongoDB: {e}")
            raise
    
    def is_connected(self):
        """Verifie si la connexion est active"""
        return self._connected
    
    def insert_one(self, document):
        """Insere un document"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        return self.collection.insert_one(document)
    
    def insert_many(self, documents):
        """Insere plusieurs documents"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        if not documents:
            return None
        return self.collection.insert_many(documents)
    
    def find(self, query=None, projection=None):
        """Recherche des documents"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        query = query or {}
        if projection:
            return list(self.collection.find(query, projection))
        return list(self.collection.find(query))
    
    def find_one(self, query):
        """Recherche un document"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        return self.collection.find_one(query)
    
    def update_one(self, query, update, upsert=False):
        """Met a jour un document"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        return self.collection.update_one(query, update, upsert=upsert)
    
    def delete_many(self, query):
        """Supprime des documents"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        return self.collection.delete_many(query)
    
    def count_documents(self, query=None):
        """Compte les documents"""
        if not self._connected:
            raise Exception("MongoDB non connecte")
        query = query or {}
        return self.collection.count_documents(query)
    
    def close(self):
        """Ferme la connexion"""
        if self.client:
            self.client.close()
            self._connected = False
            print("Connexion MongoDB fermee")


def write_scrape_status(run_dir, status_dict):
    """
    Ecrit le statut du scraping dans un fichier JSON
    
    Args:
        run_dir: Repertoire du run (Path ou str)
        status_dict: Dictionnaire contenant le statut
    """
    if not run_dir:
        return
    
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    
    status_file = run_path / 'scrape_status.json'  # Changed from status.json
    
    status_dict['updated_at'] = datetime.now().isoformat()
    
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur lors de l'ecriture du status: {e}")


def read_scrape_status(run_dir=None):
    """
    Lit le statut du scraping depuis le fichier JSON
    
    Args:
        run_dir: Repertoire du run (Path ou str). Si None, cherche le run le plus recent
    
    Returns:
        dict: Statut du scraping ou {} si non trouve
    """
    if run_dir is None:
        runs_dir = _current_file.parent.parent / 'runs'
        if not runs_dir.exists():
            return {}
        
        run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
        if not run_dirs:
            return {}
        
        run_dir = max(run_dirs, key=lambda d: d.stat().st_mtime)
    
    run_path = Path(run_dir)
    status_file = run_path / 'status.json'
    
    if not status_file.exists():
        return {}
    
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture du status: {e}")
        return {}


def get_latest_run_dir():
    """
    Retourne le repertoire du run le plus recent
    
    Returns:
        Path: Chemin du run le plus recent ou None
    """
    runs_dir = _current_file.parent.parent / 'runs'
    if not runs_dir.exists():
        return None
    
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        return None
    
    return max(run_dirs, key=lambda d: d.stat().st_mtime)


def create_run_dir():
    """
    Cree un nouveau repertoire de run avec timestamp
    
    Returns:
        Path: Chemin du repertoire cree
    """
    runs_dir = _current_file.parent.parent / 'runs'
    runs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    
    meta = {
        'run_id': timestamp,
        'created_at': datetime.now().isoformat(),
        'status': 'initialized'
    }
    
    meta_file = run_dir / 'meta.json'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    return run_dir
