"""Salva gli eventi nel database WordPress via REST API"""
import logging
import requests


class WPWriter:

    def __init__(self, config):
        self.config = config
        self.log    = logging.getLogger('wp_writer')
        self.session = requests.Session()
        self.session.auth = config.wp_auth
        self.session.headers.update({'Content-Type': 'application/json'})

    def salva_eventi(self, eventi: list) -> int:
        """Salva una lista di eventi, salta i duplicati. Ritorna il numero di nuovi salvati."""
        salvati = 0
        for ev in eventi:
            if self._salva_evento(ev):
                salvati += 1
        return salvati

    def _salva_evento(self, ev: dict) -> bool:
        url = f"{self.config.wp_api_base}/eventi"
        try:
            r = self.session.post(url, json=ev, timeout=self.config.HTTP_TIMEOUT)
            if r.status_code == 201:
                return True
            elif r.status_code == 409:
                # Duplicato — già presente
                return False
            else:
                self.log.warning(f"WP API {r.status_code}: {r.text[:200]}")
                return False
        except requests.RequestException as e:
            self.log.error(f"Errore salvataggio WP: {e}")
            return False

    def test_connessione(self) -> bool:
        """Verifica che la connessione alla WP REST API funzioni."""
        try:
            r = self.session.get(
                f"{self.config.WP_URL}/wp-json/vivirpinia/v1/eventi?limit=1",
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False
