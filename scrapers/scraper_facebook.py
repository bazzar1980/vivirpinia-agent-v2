"""Scraper Facebook Graph API — richiede FB_TOKEN in .env"""
from .base import ScraperBase


class ScraperFacebook(ScraperBase):

    API_BASE = 'https://graph.facebook.com/v19.0'

    def esegui(self) -> list:
        if not self.config.FB_TOKEN:
            self.log.warning("FB_TOKEN non configurato — scraper Facebook saltato")
            return []

        eventi = []
        for pagina in self.fonte.get('pagine', []):
            self.log.info(f"  Facebook: {pagina}")
            trovati = self._fetch_eventi(pagina)
            self.log.info(f"  → {len(trovati)} eventi da {pagina}")
            eventi.extend(trovati)
            import time; time.sleep(1)

        return eventi

    def _fetch_eventi(self, pagina_id: str) -> list:
        import requests
        url = f"{self.API_BASE}/{pagina_id}/events"
        params = {
            'access_token': self.config.FB_TOKEN,
            'fields':       'name,description,start_time,end_time,place',
            'time_filter':  'upcoming',
            'limit':        25,
        }
        try:
            r = requests.get(url, params=params, timeout=self.config.HTTP_TIMEOUT)
            data = r.json()
        except Exception as e:
            self.log.warning(f"Errore Facebook {pagina_id}: {e}")
            return []

        if 'error' in data:
            self.log.warning(f"FB API error: {data['error'].get('message', '?')}")
            return []

        eventi = []
        for ev in data.get('data', []):
            place    = ev.get('place', {})
            location = place.get('location', {})
            eventi.append({
                'titolo':      ev.get('name', ''),
                'data_raw':    ev.get('start_time', ''),
                'data_fine_raw': ev.get('end_time', ''),
                'comune':      location.get('city', ''),
                'luogo':       place.get('name', ''),
                'descrizione': self.pulisci(ev.get('description', ''), 500),
                'url':         f"https://www.facebook.com/events/{ev.get('id', '')}",
                'categoria':   self.indovina_categoria(ev.get('name', '')),
                'fonte':       self.fonte['nome'],
            })
        return eventi
