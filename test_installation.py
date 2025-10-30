"""
Script de test pour verifier l'installation et la configuration du projet.
"""

import sys
import os

# Ajout du repertoire du projet au path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test l'importation des packages essentiels."""
    print("\n=== Test 1: Importation des packages ===")
    try:
        import scrapy
        print(f"✓ Scrapy {scrapy.__version__}")
    except ImportError as e:
        print(f"✗ Scrapy non disponible: {e}")
        return False
    
    try:
        import bs4
        print(f"✓ BeautifulSoup {bs4.__version__}")
    except ImportError as e:
        print(f"✗ BeautifulSoup non disponible: {e}")
        return False
    
    try:
        import pymongo
        print(f"✓ PyMongo {pymongo.__version__}")
    except ImportError as e:
        print(f"✗ PyMongo non disponible: {e}")
        return False
    
    return True


def test_spacy():
    """Test si spaCy est disponible (optionnel)."""
    print("\n=== Test 2: spaCy (optionnel) ===")
    try:
        import spacy
        print(f"✓ spaCy {spacy.__version__} installe")
        try:
            nlp = spacy.load("fr_core_news_sm")
            print(f"✓ Modele fr_core_news_sm charge")
            return True
        except OSError:
            print("✗ Modele fr_core_news_sm non trouve")
            print("  Installation: python -m spacy download fr_core_news_sm")
            return False
    except ImportError:
        print("✗ spaCy non installe (optionnel)")
        print("  Le projet fonctionnera avec des features NLP basiques")
        return False


def test_text_features():
    """Test l'extraction de features."""
    print("\n=== Test 3: Extraction de features ===")
    try:
        from utiles import TextFeatures
        
        tf = TextFeatures(use_spacy=False)
        titre_test = "INCROYABLE ! Cette video va vous SURPRENDRE 🔥 #viral"
        features = tf.extraire_features(titre_test)
        score = tf.calculer_score_psychologique(features)
        
        print(f"✓ Titre teste: {titre_test}")
        print(f"✓ Features extraites: {len(features)} caracteristiques")
        print(f"  - Longueur: {features['longueur_caracteres']} caracteres, {features['longueur_mots']} mots")
        print(f"  - Exclamations: {features['nb_exclamations']}")
        print(f"  - Majuscules: {features['nb_majuscules']} (ratio: {features['ratio_majuscules']:.1%})")
        print(f"  - Emojis: {features['nb_emojis']}")
        print(f"  - Hashtags: {features['nb_hashtags']}")
        print(f"✓ Score psychologique: {score:.2f}/100")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'extraction de features: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mongodb():
    """Test la connexion MongoDB."""
    print("\n=== Test 4: Connexion MongoDB ===")
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        
        uri = "mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster"
        print("Tentative de connexion a MongoDB Atlas...")
        print("(Timeout: 5 secondes)")
        
        client = MongoClient(
            uri, 
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000  # 5 secondes timeout
        )
        
        # Test de ping
        client.admin.command('ping')
        print("✓ Connexion MongoDB reussie")
        
        # Test de la base de donnees
        db = client['youtube']
        collection = db['youtube']
        print(f"✓ Base de donnees: {db.name}")
        print(f"✓ Collection: {collection.name}")
        print(f"✓ Nombre de documents: {collection.count_documents({})}")
        
        client.close()
        return True
    
    except Exception as e:
        print(f"✗ Erreur de connexion MongoDB: {type(e).__name__}")
        print(f"  Message: {str(e)[:200]}")
        print("\n  Causes possibles:")
        print("  1. Connexion Internet inactive")
        print("  2. Firewall bloquant le port 27017")
        print("  3. IP non autorisee sur MongoDB Atlas")
        print("     → Aller sur https://cloud.mongodb.com/")
        print("     → Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)")
        print("  4. Credentials incorrects dans settings.py")
        return False


def test_scrapy_spider():
    """Test si le spider Scrapy est accessible."""
    print("\n=== Test 5: Spider Scrapy ===")
    try:
        from yt_title_psychology.spiders.youtube_trends import YouTubeTrendsSpider
        
        spider = YouTubeTrendsSpider()
        print(f"✓ Spider '{spider.name}' charge avec succes")
        print(f"✓ URL de depart: {spider.start_urls[0]}")
        print(f"✓ Domaines autorises: {spider.allowed_domains}")
        return True
    except Exception as e:
        print(f"✗ Erreur lors du chargement du spider: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale."""
    print("="*80)
    print("TEST D'INSTALLATION DU PROJET YOUTUBE TITLE PSYCHOLOGY".center(80))
    print("="*80)
    
    results = []
    
    # Tests essentiels
    results.append(("Packages Python", test_imports()))
    results.append(("spaCy (optionnel)", test_spacy()))
    results.append(("Extraction de features", test_text_features()))
    results.append(("Connexion MongoDB", test_mongodb()))
    results.append(("Spider Scrapy", test_scrapy_spider()))
    
    # Resume
    print("\n" + "="*80)
    print("RESUME DES TESTS".center(80))
    print("="*80)
    
    for test_name, success in results:
        status = "✓ PASSE" if success else "✗ ECHOUE"
        print(f"{test_name:.<50} {status}")
    
    # Conclusion
    essential_tests = [results[0], results[2], results[4]]  # Packages, Features, Spider
    all_essential_passed = all(success for _, success in essential_tests)
    
    print("\n" + "="*80)
    if all_essential_passed:
        print("✓ PROJET PRET A UTILISER".center(80))
        print("="*80)
        print("\nVous pouvez lancer le projet avec:")
        print("  python app.py")
        print("\nOu avec Scrapy directement:")
        print("  scrapy crawl youtube_trends -o resultats.json")
        
        if not results[3][1]:  # MongoDB echoue
            print("\nNOTE: MongoDB n'est pas accessible.")
            print("Le scraping fonctionnera mais les donnees ne seront pas stockees.")
            print("Seul l'export JSON sera disponible.")
    else:
        print("✗ PROBLEMES DETECTES".center(80))
        print("="*80)
        print("\nConsultez TROUBLESHOOTING.md pour resoudre les problemes.")
        print("Les tests essentiels doivent passer avant de lancer le projet.")
    
    print("="*80 + "\n")
    
    return 0 if all_essential_passed else 1


if __name__ == '__main__':
    sys.exit(main())
