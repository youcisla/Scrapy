"""
Spider Scrapy pour extraire les tendances YouTube mondiales depuis youtube.trends24.in.
Parse toutes les régions disponibles et extrait les métadonnées des vidéos.
"""

import scrapy
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import os

# Ajout du répertoire parent au path pour importer utiles.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utiles import TextFeatures
from yt_title_psychology.items import YouTubeTrendItem


class YouTubeTrendsSpider(scrapy.Spider):
    """
    Spider pour scraper les tendances YouTube de tous les pays sur trends24.in.
    
    Stratégie :
    1. Scrape la page principale pour détecter tous les pays/régions disponibles
    2. Pour chaque pays, extrait les vidéos tendances
    3. Parse les métadonnées (titre, URL, canal, vues, etc.)
    4. Calcule les features psychologiques avec TextFeatures
    5. Yield les items pour le pipeline MongoDB
    """
    
    name = 'youtube_trends'
    allowed_domains = ['youtube.trends24.in']
    
    # URL de départ : page mondiale
    start_urls = ['https://youtube.trends24.in/']
    
    # Initialisation de l'extracteur de features
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Politesse : 2 secondes entre les requêtes
        'CONCURRENT_REQUESTS': 1,  # Une requête à la fois
    }
    
    def __init__(self, *args, **kwargs):
        """Initialise le spider et l'extracteur de features NLP."""
        super(YouTubeTrendsSpider, self).__init__(*args, **kwargs)
        self.text_features = TextFeatures()
        self.logger.info("Spider youtube_trends initialise avec TextFeatures")
    
    def parse(self, response):
        """
        Parse la page principale pour découvrir tous les pays disponibles.
        
        Args:
            response: Réponse HTTP de la page principale
            
        Yields:
            Request: Requêtes vers les pages de chaque pays
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Recherche des liens vers les différents pays
        # Structure typique : <a href="/france/">France</a>, <a href="/usa/">USA</a>, etc.
        country_links = soup.find_all('a', href=re.compile(r'^/[a-z\-]+/$'))
        
        countries = set()
        for link in country_links:
            href = link.get('href', '')
            if href and href != '/':
                countries.add(href)
        
        self.logger.info(f"Pays detectes : {len(countries)}")
        
        # Si aucun pays détecté, scraper la page mondiale par défaut
        if not countries:
            self.logger.warning("Aucun pays detecte, scraping de la page mondiale")
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_country,
                meta={'country': 'World'}
            )
        else:
            # Scraper chaque pays
            for country_path in countries:
                country_name = country_path.strip('/').title()
                country_url = response.urljoin(country_path)
                
                self.logger.info(f"Scraping du pays : {country_name} ({country_url})")
                yield scrapy.Request(
                    url=country_url,
                    callback=self.parse_country,
                    meta={'country': country_name}
                )
    
    def parse_country(self, response):
        """
        Parse la page d'un pays pour extraire les vidéos tendances.
        
        Args:
            response: Réponse HTTP de la page du pays
            
        Yields:
            YouTubeTrendItem: Items contenant les données des vidéos
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        country = response.meta.get('country', 'Unknown')
        
        self.logger.info(f"Parsing des tendances pour : {country}")
        
        # Recherche des conteneurs de vidéos
        # Structure HTML à adapter selon le site réel
        # Sélecteurs possibles : div.video, li.trend-item, etc.
        
        # Stratégie 1 : Recherche des liens YouTube
        video_links = soup.find_all('a', href=re.compile(r'(youtube\.com/watch|youtu\.be/)'))
        
        if not video_links:
            self.logger.warning(f"Aucune video trouvee pour {country}")
            return
        
        self.logger.info(f"{len(video_links)} videos trouvees pour {country}")
        
        for link in video_links:
            try:
                # Extraction de l'URL
                url = link.get('href', '')
                if not url:
                    continue
                
                # Nettoyage de l'URL (enlever les paramètres inutiles)
                url = self._nettoyer_url(url)
                
                # Extraction du titre
                # Le titre peut être dans le texte du lien, un attribut title, ou un élément parent
                titre = link.get_text(strip=True)
                if not titre:
                    titre = link.get('title', '')
                
                # Si le titre est trop court, chercher dans l'élément parent
                if len(titre) < 5:
                    parent = link.find_parent(['div', 'li', 'article'])
                    if parent:
                        titre_elem = parent.find(['h3', 'h4', 'span', 'p'])
                        if titre_elem:
                            titre = titre_elem.get_text(strip=True)
                
                if not titre or len(titre) < 5:
                    self.logger.debug(f"Titre invalide pour {url}")
                    continue
                
                # Extraction du nom du canal
                # Généralement à côté du titre ou dans un élément avec class contenant 'channel' ou 'author'
                canal = self._extraire_canal(link)
                
                # Extraction du nombre de vues
                # Chercher des patterns comme "1.2M views", "123K vues", etc.
                vues = self._extraire_vues(link)
                
                # Extraction de l'heure/période
                # Chercher des patterns comme "2 hours ago", "il y a 3h", etc.
                heure = self._extraire_heure(link)
                
                # Calcul des features psychologiques
                features = self.text_features.extraire_features(titre)
                
                # Création de l'item
                item = YouTubeTrendItem()
                item['titre'] = titre
                item['url'] = url
                item['canal'] = canal
                item['vues'] = vues
                item['heure'] = heure
                item['pays'] = country
                item['features'] = features
                item['date_scraping'] = datetime.utcnow().isoformat()
                item['source'] = response.url
                
                yield item
            
            except Exception as e:
                self.logger.error(f"Erreur lors du parsing d'une video : {e}")
                continue
    
    def _nettoyer_url(self, url: str) -> str:
        """
        Nettoie une URL YouTube pour ne garder que l'essentiel.
        
        Args:
            url (str): URL brute
            
        Returns:
            str: URL nettoyée
        """
        # Pattern pour extraire l'ID de vidéo
        match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def _extraire_canal(self, link_element) -> str:
        """
        Extrait le nom du canal YouTube depuis l'élément HTML.
        
        Args:
            link_element: Element BeautifulSoup du lien
            
        Returns:
            str: Nom du canal ou 'Inconnu'
        """
        # Chercher dans l'élément parent
        parent = link_element.find_parent(['div', 'li', 'article'])
        if not parent:
            return 'Inconnu'
        
        # Chercher des éléments avec des mots-clés liés au canal
        for keyword in ['channel', 'author', 'uploader', 'creator']:
            canal_elem = parent.find(class_=re.compile(keyword, re.I))
            if canal_elem:
                canal = canal_elem.get_text(strip=True)
                if canal and len(canal) > 1:
                    return canal
        
        # Chercher des liens vers des pages de canal
        canal_link = parent.find('a', href=re.compile(r'/(channel|user|c)/'))
        if canal_link:
            return canal_link.get_text(strip=True)
        
        return 'Inconnu'
    
    def _extraire_vues(self, link_element) -> int:
        """
        Extrait le nombre de vues depuis l'élément HTML.
        
        Args:
            link_element: Element BeautifulSoup du lien
            
        Returns:
            int: Nombre de vues ou 0
        """
        parent = link_element.find_parent(['div', 'li', 'article'])
        if not parent:
            return 0
        
        # Chercher des patterns de vues
        text = parent.get_text()
        
        # Patterns : "1.2M views", "123K vues", "1,234,567 views"
        patterns = [
            r'([\d,\.]+)\s*([KMB])?\s*(?:views?|vues?)',
            r'([\d,\.]+)\s*(?:views?|vues?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                nombre = match.group(1).replace(',', '').replace('.', '')
                multiplicateur = match.group(2) if len(match.groups()) > 1 else None
                
                try:
                    vues = float(nombre)
                    
                    if multiplicateur:
                        if multiplicateur.upper() == 'K':
                            vues *= 1000
                        elif multiplicateur.upper() == 'M':
                            vues *= 1000000
                        elif multiplicateur.upper() == 'B':
                            vues *= 1000000000
                    
                    return int(vues)
                except ValueError:
                    continue
        
        return 0
    
    def _extraire_heure(self, link_element) -> str:
        """
        Extrait l'heure de publication ou d'apparition dans les tendances.
        
        Args:
            link_element: Element BeautifulSoup du lien
            
        Returns:
            str: Information temporelle ou 'Inconnue'
        """
        parent = link_element.find_parent(['div', 'li', 'article'])
        if not parent:
            return 'Inconnue'
        
        # Chercher des éléments avec class/id contenant 'time', 'date', 'ago'
        for keyword in ['time', 'date', 'ago', 'published']:
            time_elem = parent.find(class_=re.compile(keyword, re.I))
            if time_elem:
                heure = time_elem.get_text(strip=True)
                if heure:
                    return heure
        
        # Chercher des patterns temporels dans le texte
        text = parent.get_text()
        time_patterns = [
            r'\d+\s*(?:hour|heure|hr|h)s?\s*ago',
            r'\d+\s*(?:day|jour|jr|j)s?\s*ago',
            r'il y a \d+\s*(?:heure|jour|h|j)s?',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)
        
        return 'Inconnue'
