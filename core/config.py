"""Configurazione centralizzata — legge da variabili d'ambiente o .env"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass


class Config:
    # WordPress REST API
    WP_URL          = os.getenv('WP_URL',   'https://www.vivirpinia.it')
    WP_USER         = os.getenv('WP_USER',  'admin')
    WP_PASSWORD     = os.getenv('WP_APP_PASSWORD', '')  # Application Password WP

    # Facebook Graph API (opzionale)
    FB_TOKEN        = os.getenv('FB_TOKEN', '')

    # Timeout richieste HTTP (secondi)
    HTTP_TIMEOUT    = int(os.getenv('HTTP_TIMEOUT', '20'))

    # User-Agent
    USER_AGENT      = 'VivIrpiniaBot/2.0 (+https://www.vivirpinia.it/bot)'

    # Pausa tra richieste (secondi)
    REQUEST_DELAY   = float(os.getenv('REQUEST_DELAY', '2'))

    @property
    def wp_api_base(self):
        return f"{self.WP_URL.rstrip('/')}/wp-json/vivirpinia/v1"

    @property
    def wp_auth(self):
        return (self.WP_USER, self.WP_PASSWORD)
