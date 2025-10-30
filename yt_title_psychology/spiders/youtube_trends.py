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

# Import from yt_title_psychology package
from yt_title_psychology.utiles import TextFeatures, write_scrape_status
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
    # allow following to YouTube pages to enrich metadata
    allowed_domains.extend(['www.youtube.com', 'youtube.com', 'youtu.be'])
    # URL de départ : page mondiale
    start_urls = ['https://youtube.trends24.in/']
    
    # Initialisation de l'extracteur de features
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Politesse : 2 secondes entre les requêtes
        'CONCURRENT_REQUESTS': 1,  # Une requête à la fois
    }
    
    def __init__(self, *args, **kwargs):
        """Initialise le spider."""
        super(YouTubeTrendsSpider, self).__init__(*args, **kwargs)
        self.logger.info("Spider youtube_trends initialise")
        # Progress tracking
        self._countries_total = None
        self._countries_done = 0
        self._items_scraped = 0
        self._current_country = None
        self._run_dir = os.environ.get('SCRAPE_RUN_DIR')
        # initial status
        try:
            write_scrape_status(self._run_dir, {
                'started_at': datetime.now().isoformat(),
                'countries_total': None,
                'countries_done': 0,
                'items_scraped': 0,
                'current_country': None,
                'status': 'running'
            })
        except Exception as e:
            self.logger.warning(f"Failed to write initial status: {e}")
    
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
        # update total
        try:
            self._countries_total = len(countries) if countries else 1
            write_scrape_status(self._run_dir, {
                'started_at': datetime.now().isoformat(),
                'countries_total': self._countries_total,
                'countries_done': self._countries_done,
                'items_scraped': self._items_scraped,
                'current_country': None,
                'status': 'running'
            })
        except Exception as e:
            self.logger.warning(f"Failed to write status: {e}")
        
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
            # Still increment countries_done even if no videos
            self._countries_done += 1
            return
        
        self.logger.info(f"{len(video_links)} videos trouvees pour {country}")
        
        # Update current country
        self._current_country = country
        
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
                
                # Prepare a base item payload and follow to the YouTube page to enrich metadata
                base = {
                    'titre': titre,
                    'url': url,
                    'canal': canal,
                    'vues': vues,
                    'heure': heure,
                    'pays': country,
                    'date_scraping': datetime.now().isoformat(),
                    'source': response.url
                }

                # increment counter and persist progress before following
                try:
                    self._items_scraped += 1
                    write_scrape_status(self._run_dir, {
                        'started_at': datetime.now().isoformat(),
                        'countries_total': self._countries_total,
                        'countries_done': self._countries_done,
                        'items_scraped': self._items_scraped,
                        'current_country': self._current_country,
                        'status': 'running'
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to write status: {e}")

                # Skip fetching individual video pages for speed - just yield the base item
                # The duration and other metadata will be missing, but scraping is much faster
                yield base
                
                # DISABLED: Follow the YouTube URL to extract channel/views/publish time
                # This makes scraping very slow (276 additional requests)
                # yield scrapy.Request(url, callback=self.parse_video, meta={'base': base}, dont_filter=True)
            
            except Exception as e:
                self.logger.error(f"Erreur lors du parsing d'une video : {e}")
                continue
        
        # Finished this country - increment AFTER processing all videos
        try:
            self._countries_done += 1
            write_scrape_status(self._run_dir, {
                'started_at': datetime.now().isoformat(),
                'countries_total': self._countries_total,
                'countries_done': self._countries_done,
                'items_scraped': self._items_scraped,
                'current_country': None,
                'status': 'running'
            })
        except Exception as e:
            self.logger.warning(f"Failed to write status: {e}")
            
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

    def closed(self, reason):
        """Called when the spider finishes or is closed; write final status."""
        try:
            write_scrape_status(self._run_dir, {
                'started_at': datetime.now().isoformat(),
                'finished_at': datetime.now().isoformat(),
                'countries_total': self._countries_total,
                'countries_done': self._countries_done,
                'items_scraped': self._items_scraped,
                'current_country': None,
                'status': 'finished',
                'reason': str(reason)
            })
        except Exception as e:
            self.logger.warning(f"Failed to write final status: {e}")

    def parse_video(self, response):
        """Parse a YouTube video page to enrich metadata (channel, views, published date).

        This is best-effort: YouTube pages are JS-heavy, but some metadata is present
        in initial HTML meta tags or in inline JSON.
        """
        base = response.meta.get('base', {})
        try:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # Channel: try meta[name='author'] or link rel="author"
            canal = base.get('canal') or ''
            m = soup.find('meta', attrs={'name': 'author'})
            if m and m.get('content'):
                canal = m.get('content')

            # Views: try meta[itemprop='interactionCount'] or look for "viewCount" in the page JSON
            vues = base.get('vues') or 0
            mv = soup.find('meta', itemprop='interactionCount')
            if mv and mv.get('content'):
                try:
                    vues = int(mv.get('content'))
                except Exception:
                    pass

            if vues == 0:
                # fallback: search for "viewCount":"12345" pattern
                m2 = re.search(r'"viewCount"\s*:\s*"?(\d{1,3}(?:[,\.\d]*)?)"?', html)
                if m2:
                    n = m2.group(1).replace(',', '').replace('.', '')
                    try:
                        vues = int(n)
                    except Exception:
                        pass

            # Published date: meta[itemprop='datePublished']
            heure = base.get('heure') or 'Inconnue'
            md = soup.find('meta', itemprop='datePublished')
            if md and md.get('content'):
                heure = md.get('content')
            
            # Video duration: meta[itemprop='duration'] or look for "lengthSeconds" in JSON
            duree = base.get('duree') or '0'
            md_duration = soup.find('meta', itemprop='duration')
            if md_duration and md_duration.get('content'):
                # ISO 8601 duration format: PT1M30S = 1 minute 30 seconds
                duration_str = md_duration.get('content')
                try:
                    # Parse ISO 8601 duration (e.g., PT1H2M30S)
                    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
                    if match:
                        hours = int(match.group(1) or 0)
                        minutes = int(match.group(2) or 0)
                        seconds = int(match.group(3) or 0)
                        duree = str(hours * 3600 + minutes * 60 + seconds)
                except Exception:
                    pass
            
            if duree == '0':
                # fallback: search for "lengthSeconds":"123" pattern
                m_length = re.search(r'"lengthSeconds"\s*:\s*"?(\d+)"?', html)
                if m_length:
                    duree = m_length.group(1)

            # Extract features from title
            titre = base.get('titre', '')
            features = TextFeatures(titre).get_all_features() if titre else {}

            item = YouTubeTrendItem()
            item['titre'] = base.get('titre')
            item['url'] = base.get('url')
            item['canal'] = canal or base.get('canal', 'Inconnu')
            item['vues'] = vues
            item['heure'] = heure
            item['duree'] = duree
            item['pays'] = base.get('pays')
            item['features'] = features
            item['date_scraping'] = base.get('date_scraping')
            item['source'] = base.get('source')

            yield item

        except Exception as e:
            self.logger.debug(f"Impossible d'enrichir la page YouTube: {e}")
            # fallback to base item
            item = YouTubeTrendItem()
            for k, v in base.items():
                item[k] = v
            titre = base.get('titre', '')
            item['features'] = TextFeatures(titre).get_all_features() if titre else {}
            item['duree'] = item.get('duree', '0')
            yield item
