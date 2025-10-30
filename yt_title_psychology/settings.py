"""
Configuration Scrapy pour le projet d'analyse des tendances YouTube.
"""

BOT_NAME = "yt_title_psychology"

SPIDER_MODULES = ["yt_title_psychology.spiders"]
NEWSPIDER_MODULE = "yt_title_psychology.spiders"


# Respecter les règles de politesse du web
# User-Agent explicite pour identifier le bot
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 YoutubeTrendAnalyzer/1.0"

# Respecter robots.txt
ROBOTSTXT_OBEY = False  # trends24.in n'a pas de robots.txt strict pour le scraping

# Configuration des requêtes simultanées
CONCURRENT_REQUESTS = 4  # Nombre de requêtes simultanées maximum

# Délai de téléchargement (en secondes)
# Attendre entre 1 et 2 secondes entre chaque requête pour être poli
DOWNLOAD_DELAY = 1.5
# Le délai peut aussi être aléatoire avec :
# RANDOMIZE_DOWNLOAD_DELAY = True

# Désactiver les cookies (pas nécessaire pour ce scraping)
COOKIES_ENABLED = False

# Désactiver Telnet Console (pour la sécurité)
TELNETCONSOLE_ENABLED = False

# Configuration des pipelines
# Les nombres représentent l'ordre d'exécution (300-1000)
ITEM_PIPELINES = {
    "yt_title_psychology.pipelines.YoutubeTrendsPipeline": 300,  # Validation d'abord
    "yt_title_psychology.pipelines.MongoDBPipeline": 400,  # Stockage ensuite
}

# Configuration MongoDB Atlas
# URI de connexion à MongoDB Atlas
MONGO_URI = "mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster"

# Nom de la base de données
MONGO_DATABASE = "youtube"

# Nom de la collection
MONGO_COLLECTION = "youtube"

# Configuration AutoThrottle pour adapter automatiquement la vitesse
# de scraping en fonction de la charge du serveur
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1  # Délai initial
AUTOTHROTTLE_MAX_DELAY = 5  # Délai maximum
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0  # Nombre moyen de requêtes simultanées
AUTOTHROTTLE_DEBUG = False  # Afficher les statistiques AutoThrottle

# Configuration du cache HTTP (optionnel, pour le développement)
# Permet de ne pas refaire les requêtes déjà effectuées
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600  # 1 heure
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Configuration des logs
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# Encodage par défaut
FEED_EXPORT_ENCODING = "utf-8"

# Configuration des exports JSON
FEED_EXPORT_INDENT = 2  # Indentation pour la lisibilité

# Retry configuration (réessayer en cas d'échec)
RETRY_ENABLED = True
RETRY_TIMES = 3  # Nombre de tentatives
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]  # Codes HTTP à réessayer

# Timeout des requêtes
DOWNLOAD_TIMEOUT = 30  # 30 secondes

# Configuration des middlewares (si nécessaire)
# DOWNLOADER_MIDDLEWARES = {
#     "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
#     "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
# }

# Configuration des extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,  # Désactiver Telnet
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
