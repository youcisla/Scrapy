"""
Définition des Items Scrapy pour le projet d'analyse des titres YouTube.
Chaque item représente une vidéo tendance avec ses métadonnées et features psychologiques.
"""

import scrapy


class YouTubeTrendItem(scrapy.Item):
    """
    Item représentant une vidéo tendance YouTube.
    
    Champs principaux :
    - titre : Le titre complet de la vidéo
    - url : Lien vers la vidéo YouTube
    - canal : Nom de la chaîne YouTube
    - vues : Nombre de vues (format int)
    - heure : Horodatage ou période d'apparition dans les tendances
    - pays : Pays de la tendance (France, USA, World, etc.)
    - features : Dictionnaire contenant les caractéristiques psychologiques du titre
    """
    
    # Métadonnées de la vidéo
    titre = scrapy.Field()
    url = scrapy.Field()
    canal = scrapy.Field()
    vues = scrapy.Field()
    heure = scrapy.Field()
    pays = scrapy.Field()
    
    # Dictionnaire des features psychologiques
    # Structure : {
    #   'longueur_caracteres': int,
    #   'longueur_mots': int,
    #   'nb_majuscules': int,
    #   'nb_emojis': int,
    #   'nb_chiffres': int,
    #   'nb_interrogations': int,
    #   'nb_exclamations': int,
    #   'ratio_majuscules': float,
    #   'nb_hashtags': int,
    #   'langue_detectee': str,
    #   'tonalite_moyenne': float
    # }
    features = scrapy.Field()
    
    # Métadonnées de scraping
    date_scraping = scrapy.Field()
    source = scrapy.Field()
