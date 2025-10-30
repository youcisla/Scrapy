"""
Classes utilitaires pour l'analyse NLP des titres et la gestion de MongoDB.
"""

import re
import unicodedata
from typing import Dict, Any
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import logging

# Configuration du logger
logger = logging.getLogger(__name__)


class TextFeatures:
    """
    Classe pour extraire les caractéristiques psychologiques d'un texte (titre).
    Utilise des regex et spaCy pour l'analyse linguistique.
    """
    
    def __init__(self, use_spacy=True):
        """
        Initialise le modèle spaCy pour le français (optionnel).
        Charge le modèle fr_core_news_sm (léger et rapide) si disponible.
        
        Args:
            use_spacy (bool): Si True, tente de charger spaCy. Si False, utilise uniquement regex.
        """
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("fr_core_news_sm")
                logger.info("Modele spaCy charge avec succes")
            except ImportError:
                logger.warning("spaCy n'est pas installe. Installation : pip install spacy && python -m spacy download fr_core_news_sm")
            except OSError:
                logger.warning("Modele spaCy fr_core_news_sm non trouve. Installation : python -m spacy download fr_core_news_sm")
            except Exception as e:
                logger.warning(f"Impossible de charger spaCy : {e}. Les features NLP seront limitees.")
        else:
            logger.info("Mode sans spaCy active. Analyse NLP basique uniquement.")
    
    def nettoyer_texte(self, texte: str) -> str:
        """
        Nettoie un texte en normalisant les caractères Unicode et en supprimant
        les caractères de contrôle.
        
        Args:
            texte (str): Le texte à nettoyer
            
        Returns:
            str: Le texte nettoyé
        """
        if not texte:
            return ""
        
        # Normalisation Unicode (forme NFC)
        texte = unicodedata.normalize('NFC', texte)
        
        # Suppression des caractères de contrôle
        texte = ''.join(char for char in texte if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        # Strip des espaces
        texte = texte.strip()
        
        return texte
    
    def compter_emojis(self, texte: str) -> int:
        """
        Compte le nombre d'emojis dans un texte.
        Utilise les plages Unicode des emojis.
        
        Args:
            texte (str): Le texte à analyser
            
        Returns:
            int: Nombre d'emojis trouvés
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symboles & pictogrammes
            "\U0001F680-\U0001F6FF"  # Transport & symboles de carte
            "\U0001F1E0-\U0001F1FF"  # Drapeaux (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return len(emoji_pattern.findall(texte))
    
    def detecter_langue(self, texte: str) -> str:
        """
        Détecte la langue prédominante du texte (FR ou EN).
        Méthode simple basée sur des mots courants.
        
        Args:
            texte (str): Le texte à analyser
            
        Returns:
            str: Code de langue ('FR', 'EN', ou 'AUTRE')
        """
        texte_lower = texte.lower()
        
        # Mots français courants
        mots_fr = ['le', 'la', 'les', 'de', 'des', 'et', 'pour', 'avec', 'dans', 'ce', 'qui', 'que']
        # Mots anglais courants
        mots_en = ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'what', 'how', 'why']
        
        score_fr = sum(1 for mot in mots_fr if f' {mot} ' in f' {texte_lower} ')
        score_en = sum(1 for mot in mots_en if f' {mot} ' in f' {texte_lower} ')
        
        if score_fr > score_en:
            return 'FR'
        elif score_en > score_fr:
            return 'EN'
        else:
            return 'AUTRE'
    
    def calculer_tonalite(self, texte: str) -> float:
        """
        Calcule une tonalité moyenne basée sur l'analyse morphosyntaxique spaCy.
        Score simple basé sur les catégories POS (Part-Of-Speech).
        
        Args:
            texte (str): Le texte à analyser
            
        Returns:
            float: Score de tonalité entre 0 et 1
        """
        if not self.nlp or not texte:
            return 0.5
        
        try:
            doc = self.nlp(texte)
            
            # Comptage des catégories POS
            # ADJ: adjectifs (peuvent indiquer émotion)
            # VERB: verbes d'action
            # NOUN: noms (neutre)
            nb_adj = sum(1 for token in doc if token.pos_ == 'ADJ')
            nb_verb = sum(1 for token in doc if token.pos_ == 'VERB')
            nb_total = len(doc)
            
            if nb_total == 0:
                return 0.5
            
            # Score simple : plus d'adjectifs/verbes = tonalité plus émotionnelle
            score = (nb_adj * 0.6 + nb_verb * 0.4) / nb_total
            return min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Erreur lors du calcul de tonalite : {e}")
            return 0.5
    
    def extraire_features(self, titre: str) -> Dict[str, Any]:
        """
        Extrait toutes les caractéristiques psychologiques d'un titre.
        
        Args:
            titre (str): Le titre de la vidéo
            
        Returns:
            Dict[str, Any]: Dictionnaire contenant toutes les features
        """
        # Nettoyage du titre
        titre_clean = self.nettoyer_texte(titre)
        
        if not titre_clean:
            return self._features_vides()
        
        # Calculs de base
        longueur_caracteres = len(titre_clean)
        mots = titre_clean.split()
        longueur_mots = len(mots)
        
        # Comptage des caractères spéciaux
        nb_majuscules = sum(1 for c in titre_clean if c.isupper())
        nb_chiffres = sum(1 for c in titre_clean if c.isdigit())
        nb_interrogations = titre_clean.count('?')
        nb_exclamations = titre_clean.count('!')
        nb_hashtags = titre_clean.count('#')
        
        # Ratio de majuscules
        nb_lettres = sum(1 for c in titre_clean if c.isalpha())
        ratio_majuscules = (nb_majuscules / nb_lettres) if nb_lettres > 0 else 0.0
        
        # Emojis
        nb_emojis = self.compter_emojis(titre_clean)
        
        # Langue
        langue_detectee = self.detecter_langue(titre_clean)
        
        # Tonalité (nécessite spaCy)
        tonalite_moyenne = self.calculer_tonalite(titre_clean)
        
        return {
            'longueur_caracteres': longueur_caracteres,
            'longueur_mots': longueur_mots,
            'nb_majuscules': nb_majuscules,
            'nb_emojis': nb_emojis,
            'nb_chiffres': nb_chiffres,
            'nb_interrogations': nb_interrogations,
            'nb_exclamations': nb_exclamations,
            'ratio_majuscules': round(ratio_majuscules, 3),
            'nb_hashtags': nb_hashtags,
            'langue_detectee': langue_detectee,
            'tonalite_moyenne': round(tonalite_moyenne, 3)
        }
    
    def _features_vides(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire de features vides/par défaut.
        
        Returns:
            Dict[str, Any]: Features avec valeurs par défaut
        """
        return {
            'longueur_caracteres': 0,
            'longueur_mots': 0,
            'nb_majuscules': 0,
            'nb_emojis': 0,
            'nb_chiffres': 0,
            'nb_interrogations': 0,
            'nb_exclamations': 0,
            'ratio_majuscules': 0.0,
            'nb_hashtags': 0,
            'langue_detectee': 'AUTRE',
            'tonalite_moyenne': 0.5
        }
    
    def calculer_score_psychologique(self, features: Dict[str, Any]) -> float:
        """
        Calcule un score psychologique global basé sur les features.
        Plus le score est élevé, plus le titre est "accrocheur".
        
        Args:
            features (Dict[str, Any]): Dictionnaire des features
            
        Returns:
            float: Score psychologique entre 0 et 100
        """
        score = 0.0
        
        # Points pour les caractères d'émotion
        score += features['nb_exclamations'] * 5
        score += features['nb_interrogations'] * 3
        score += features['nb_emojis'] * 4
        
        # Points pour les majuscules (attention, modéré)
        score += min(features['ratio_majuscules'] * 20, 15)
        
        # Points pour les chiffres (titres avec chiffres attirent l'attention)
        score += min(features['nb_chiffres'] * 2, 10)
        
        # Points pour la longueur optimale (30-60 caractères)
        if 30 <= features['longueur_caracteres'] <= 60:
            score += 10
        
        # Points pour la tonalité émotionnelle
        score += features['tonalite_moyenne'] * 15
        
        # Bonus hashtags
        score += min(features['nb_hashtags'] * 3, 10)
        
        return round(min(score, 100), 2)


class MongoClientWrapper:
    """
    Wrapper pour la gestion simplifiée de MongoDB Atlas.
    Gère la connexion, l'insertion et la mise à jour des documents.
    """
    
    def __init__(self, uri: str, db_name: str, collection_name: str):
        """
        Initialise la connexion à MongoDB Atlas.
        
        Args:
            uri (str): URI de connexion MongoDB Atlas
            db_name (str): Nom de la base de données
            collection_name (str): Nom de la collection
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """
        Établit la connexion à MongoDB Atlas.
        Lève une exception en cas d'échec.
        """
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            # Test de connexion
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connexion reussie a MongoDB : {self.db_name}.{self.collection_name}")
        except Exception as e:
            logger.error(f"Erreur de connexion a MongoDB : {e}")
            raise
    
    def insert_or_update(self, document: dict) -> bool:
        """
        Insère un document ou le met à jour s'il existe déjà.
        La clé unique est l'URL de la vidéo.
        
        Args:
            document (dict): Document à insérer/mettre à jour
            
        Returns:
            bool: True si succès, False sinon
        """
        if not self.collection:
            logger.error("Collection non initialisee")
            return False
        
        try:
            # Utilisation de l'URL comme clé unique
            filter_query = {'url': document.get('url')}
            
            # Upsert : mise à jour si existe, insertion sinon
            result = self.collection.update_one(
                filter_query,
                {'$set': document},
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Document insere : {document.get('url')}")
            else:
                logger.debug(f"Document mis a jour : {document.get('url')}")
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion/mise a jour : {e}")
            return False
    
    def close(self):
        """
        Ferme la connexion MongoDB proprement.
        """
        if self.client:
            self.client.close()
            logger.info("Connexion MongoDB fermee")
