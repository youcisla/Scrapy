"""
Pipelines Scrapy pour le traitement et le stockage des items.
Pipeline MongoDB pour insérer/mettre à jour les vidéos dans MongoDB Atlas.
"""

from itemadapter import ItemAdapter
from datetime import datetime
import logging
import sys
import os

# Ajout du répertoire parent au path pour importer utiles.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utiles import MongoClientWrapper, TextFeatures

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
        self.text_features = TextFeatures()
    
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
                db_name=self.mongo_db,
                collection_name=self.mongo_collection
            )
            self.mongo_client.connect()
            logger.info("Pipeline MongoDB initialise avec succes")
        except Exception as e:
            logger.warning(f"MongoDB non accessible : {e}")
            logger.warning("Le scraping continuera mais les donnees ne seront pas stockees dans MongoDB")
            logger.warning("Seul l'export JSON sera disponible")
            self.mongo_client = None  # Désactiver MongoDB pour cette session
    
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
            'pays': adapter.get('pays'),
            'features': adapter.get('features', {}),
            'date_scraping': adapter.get('date_scraping'),
            'source': adapter.get('source'),
        }
        
        # Ajout du score psychologique
        if document['features']:
            document['score_psychologique'] = self.text_features.calculer_score_psychologique(
                document['features']
            )
        else:
            document['score_psychologique'] = 0
        
        # Insertion/mise à jour dans MongoDB (si disponible)
        if self.mongo_client is None:
            # MongoDB non disponible, on passe l'item sans le stocker
            logger.debug(f"MongoDB desactive, item non stocke : {document['url']}")
            return item
        
        try:
            # Vérifier si le document existe déjà
            existing = self.mongo_client.collection.find_one({'url': document['url']})
            
            success = self.mongo_client.insert_or_update(document)
            
            if success:
                self.items_processed += 1
                if existing:
                    self.items_updated += 1
                else:
                    self.items_inserted += 1
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage de l'item {document['url']} : {e}")
        
        return item


class DropItem(Exception):
    """Exception levée pour supprimer un item du pipeline."""
    pass
