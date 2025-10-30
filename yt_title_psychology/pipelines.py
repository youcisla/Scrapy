"""
Pipelines Scrapy pour le traitement et le stockage des items.
Pipeline MongoDB pour insérer/mettre à jour les vidéos dans MongoDB Atlas.
"""

from itemadapter import ItemAdapter
from datetime import datetime
import logging
import sys
import os
import json
from pathlib import Path

# Import from yt_title_psychology package
from yt_title_psychology.utiles import MongoClientWrapper, TextFeatures

logger = logging.getLogger(__name__)


class YoutubeTrendsPipeline:
    """
    Pipeline de base pour nettoyer et valider les items scrapés.
    S'assure que tous les champs requis sont présents et valides.
    """
    
    def process_item(self, item, spider):
        """
        Traite et valide chaque item avant stockage.
        
        Args:
            item: Item Scrapy à traiter
            spider: Instance du spider
            
        Returns:
            Item: Item traité et validé
        """
        adapter = ItemAdapter(item)
        
        # Validation du titre
        if not adapter.get('titre'):
            raise DropItem("Titre manquant")
        
        # Validation de l'URL
        if not adapter.get('url'):
            raise DropItem("URL manquante")
        
        # Valeurs par défaut pour les champs optionnels
        if not adapter.get('canal'):
            adapter['canal'] = 'Inconnu'
        
        if not adapter.get('vues'):
            adapter['vues'] = 0
        
        if not adapter.get('heure'):
            adapter['heure'] = 'Inconnue'
        
        if not adapter.get('pays'):
            adapter['pays'] = 'World'
        
        # Validation des features
        if not adapter.get('features'):
            logger.warning(f"Features manquantes pour {adapter['url']}")
            adapter['features'] = {}
        
        return item


class MongoDBPipeline:
    """
    Pipeline pour stocker les items dans MongoDB Atlas.
    Gère la connexion, l'insertion et la mise à jour des doublons.
    """
    
    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        """
        Initialise le pipeline avec les paramètres MongoDB.
        
        Args:
            mongo_uri (str): URI de connexion MongoDB Atlas
            mongo_db (str): Nom de la base de données
            mongo_collection (str): Nom de la collection
        """
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.mongo_client = None
        self.items_processed = 0
        self.items_inserted = 0
        self.items_updated = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        """
        Méthode factory pour créer le pipeline depuis les settings Scrapy.
        
        Args:
            crawler: Instance du crawler Scrapy
            
        Returns:
            MongoDBPipeline: Instance du pipeline configuré
        """
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'youtube'),
            mongo_collection=crawler.settings.get('MONGO_COLLECTION', 'youtube')
        )
    
    def open_spider(self, spider):
        """
        Appelé à l'ouverture du spider.
        Établit la connexion à MongoDB (optionnel - le scraping continue même en cas d'échec).
        
        Args:
            spider: Instance du spider
        """
        try:
            self.mongo_client = MongoClientWrapper(
                uri=self.mongo_uri,
                database_name=self.mongo_db,
                collection_name=self.mongo_collection
            )
            self.mongo_client.connect()
            logger.info("Pipeline MongoDB initialise avec succes")
        except Exception as e:
            logger.warning(f"MongoDB non accessible : {e}")
            logger.warning("Le scraping continuera mais les donnees ne seront pas stockees dans MongoDB")
            logger.warning("Seul l'export JSON sera disponible")
            self.mongo_client = None  # Désactiver MongoDB pour cette session
        # Prepare local fallback storage (per-run if SCRAPE_RUN_DIR set)
        run_dir = os.environ.get('SCRAPE_RUN_DIR')
        self._local_docs = []
        if run_dir:
            self._local_out = Path(run_dir) / 'tendances_youtube.json'
        else:
            self._local_out = Path('tendances_youtube.json')
    
    def close_spider(self, spider):
        """
        Appelé à la fermeture du spider.
        Ferme la connexion MongoDB et affiche les statistiques.
        
        Args:
            spider: Instance du spider
        """
        if self.mongo_client is not None:
            self.mongo_client.close()
        
        logger.info(f"Pipeline MongoDB ferme. Stats :")
        logger.info(f"  - Items traites : {self.items_processed}")
        logger.info(f"  - Items inseres : {self.items_inserted}")
        logger.info(f"  - Items mis a jour : {self.items_updated}")
        # If MongoDB was not available, persist local docs to JSON (merge by URL)
        try:
            if self.mongo_client is None and getattr(self, '_local_docs', None):
                # load existing if present
                existing = []
                if self._local_out.exists():
                    try:
                        existing = json.loads(self._local_out.read_text(encoding='utf-8'))
                    except Exception:
                        existing = []

                # index by url
                idx = {doc.get('url'): doc for doc in existing}
                for doc in self._local_docs:
                    idx[doc.get('url')] = doc

                merged = list(idx.values())
                try:
                    self._local_out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
                    logger.info(f"Export local ecrit: {self._local_out}")
                except Exception as e:
                    logger.error(f"Impossible d'ecrire l'export local: {e}")
        except Exception:
            pass
    
    def process_item(self, item, spider):
        """
        Traite chaque item et le stocke dans MongoDB.
        
        Args:
            item: Item Scrapy à traiter
            spider: Instance du spider
            
        Returns:
            Item: Item traité
        """
        adapter = ItemAdapter(item)
        
        # Conversion de l'item en dictionnaire pour MongoDB
        document = {
            'titre': adapter.get('titre'),
            'url': adapter.get('url'),
            'canal': adapter.get('canal'),
            'vues': adapter.get('vues'),
            'heure': adapter.get('heure'),
            'duree': adapter.get('duree', '0'),
            'pays': adapter.get('pays'),
            'features': adapter.get('features', {}),
            'date_scraping': adapter.get('date_scraping'),
            'source': adapter.get('source'),
        }
        
        # Calculate psychological score from features
        if document['features']:
            features = document['features']
            # Simple score calculation based on feature values
            score = (
                features.get('caps_count', 0) * 0.5 +
                features.get('exclamation_count', 0) * 2 +
                features.get('question_count', 0) * 1.5 +
                (10 if features.get('has_emoji') else 0) +
                (5 if features.get('has_clickbait_words') else 0)
            )
            document['score_psychologique'] = min(100, score)  # Cap at 100
        else:
            document['score_psychologique'] = 0
        
        # Insertion/mise à jour dans MongoDB (si disponible)
        if self.mongo_client is None:
            # MongoDB non disponible, on passe l'item sans le stocker
            logger.debug(f"MongoDB desactive, stockage local: {document['url']}")
            try:
                self._local_docs.append(document)
            except Exception:
                pass
            return item
        
        try:
            # Upsert: insert if not exists, update if exists
            result = self.mongo_client.update_one(
                {'url': document['url']},
                {'$set': document},
                upsert=True
            )
            
            self.items_processed += 1
            if result.upserted_id:
                self.items_inserted += 1
                logger.debug(f"Document insere: {document['url']}")
            else:
                self.items_updated += 1
                logger.debug(f"Document mis a jour: {document['url']}")
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage de l'item {document['url']} : {e}")
        
        return item


class DropItem(Exception):
    """Exception levée pour supprimer un item du pipeline."""
    pass
