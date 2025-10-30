"""
Point d'entree principal pour lancer le spider et afficher les resultats.
Permet d'executer le spider depuis Python plutot que la ligne de commande.
"""

import subprocess
import sys
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import logging
from utiles import TextFeatures

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def lancer_spider(output_file='trending_fr.json'):
    """
    Lance le spider Scrapy avec export JSON.
    
    Args:
        output_file (str): Nom du fichier JSON de sortie
    """
    logger.info("Demarrage du spider youtube_trends...")
    
    try:
        # Construction de la commande Scrapy
        cmd = [
            'scrapy', 'crawl', 'youtube_trends',
            '-o', output_file
        ]
        
        # Execution de la commande
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Spider execute avec succes. Resultats exportes dans {output_file}")
            return True
        else:
            logger.error(f"Erreur lors de l'execution du spider : {result.stderr}")
            return False
    
    except FileNotFoundError:
        logger.error("Scrapy n'est pas installe ou n'est pas dans le PATH")
        logger.info("Installez Scrapy avec : pip install scrapy")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        return False


def afficher_top_titres(mongo_uri, db_name='youtube', collection_name='youtube', top_n=5):
    """
    Affiche les top N titres avec les scores psychologiques les plus eleves.
    
    Args:
        mongo_uri (str): URI de connexion MongoDB
        db_name (str): Nom de la base de donnees
        collection_name (str): Nom de la collection
        top_n (int): Nombre de titres a afficher
    """
    logger.info(f"\nRecuperation du top {top_n} des titres les plus accrocheurs...")
    
    try:
        # Connexion a MongoDB
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        db = client[db_name]
        collection = db[collection_name]
        
        # Recuperation des top titres tries par score psychologique
        top_titres = collection.find().sort('score_psychologique', -1).limit(top_n)
        
        text_features = TextFeatures()
        
        print("\n" + "="*80)
        print(f"TOP {top_n} DES TITRES LES PLUS ACCROCHEURS".center(80))
        print("="*80 + "\n")
        
        for i, video in enumerate(top_titres, 1):
            score = video.get('score_psychologique', 0)
            titre = video.get('titre', 'N/A')
            pays = video.get('pays', 'N/A')
            canal = video.get('canal', 'N/A')
            vues = video.get('vues', 0)
            features = video.get('features', {})
            
            print(f"{i}. Score psychologique : {score:.2f}/100")
            print(f"   Titre : {titre}")
            print(f"   Canal : {canal}")
            print(f"   Pays : {pays}")
            print(f"   Vues : {vues:,}".replace(',', ' '))
            print(f"   URL : {video.get('url', 'N/A')}")
            
            # Affichage des features principales
            if features:
                print(f"   Features :")
                print(f"     - Longueur : {features.get('longueur_caracteres', 0)} caracteres, {features.get('longueur_mots', 0)} mots")
                print(f"     - Exclamations : {features.get('nb_exclamations', 0)} | Interrogations : {features.get('nb_interrogations', 0)}")
                print(f"     - Emojis : {features.get('nb_emojis', 0)} | Hashtags : {features.get('nb_hashtags', 0)}")
                print(f"     - Ratio majuscules : {features.get('ratio_majuscules', 0):.1%}")
                print(f"     - Langue : {features.get('langue_detectee', 'N/A')}")
                print(f"     - Tonalite : {features.get('tonalite_moyenne', 0):.2f}")
            
            print("-" * 80)
        
        # Statistiques globales
        total_videos = collection.count_documents({})
        print(f"\nTotal de videos dans la base : {total_videos}")
        
        # Statistiques par pays
        print("\nRepartition par pays :")
        pays_stats = collection.aggregate([
            {'$group': {'_id': '$pays', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        for stat in pays_stats:
            print(f"  - {stat['_id']} : {stat['count']} videos")
        
        client.close()
    
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des donnees MongoDB : {e}")


def main():
    """
    Fonction principale du programme.
    """
    print("\n" + "="*80)
    print("ANALYSEUR DE PSYCHOLOGIE DES TITRES YOUTUBE".center(80))
    print("="*80 + "\n")
    
    # Configuration MongoDB
    mongo_uri = "mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster"
    db_name = "youtube"
    collection_name = "youtube"
    
    # Menu interactif
    print("Options disponibles :")
    print("1. Lancer le spider et scraper les tendances")
    print("2. Afficher le top 5 des titres les plus accrocheurs")
    print("3. Les deux (scraping puis affichage)")
    print("4. Quitter")
    
    choix = input("\nVotre choix (1-4) : ").strip()
    
    if choix == '1':
        lancer_spider()
    
    elif choix == '2':
        afficher_top_titres(mongo_uri, db_name, collection_name)
    
    elif choix == '3':
        success = lancer_spider()
        if success:
            print("\nAttente de quelques secondes pour la synchronisation MongoDB...")
            import time
            time.sleep(3)
            afficher_top_titres(mongo_uri, db_name, collection_name)
    
    elif choix == '4':
        print("Au revoir !")
        sys.exit(0)
    
    else:
        print("Choix invalide. Relancez le programme.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("Fin du programme".center(80))
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
