"""Classe base per tutti gli scraper"""
import logging
import re
import time
from datetime import datetime

import requests


class ScraperBase:
    def __init__(self, fonte: dict, config):
        self.fonte  = fonte
        self.config = config
        self.log    = logging.getLogger(f"scraper.{fonte['id']}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':      config.USER_AGENT,
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.5',
        })

    def esegui(self) -> list:
        raise NotImplementedError

    def fetch(self, url: str) -> str | None:
        try:
            r = self.session.get(url, timeout=self.config.HTTP_TIMEOUT)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            self.log.warning(f"Fetch fallita {url}: {e}")
            return None

    def pulisci(self, html: str, max_len: int = 500) -> str:
        """Rimuove tag HTML e normalizza spazi."""
        text = re.sub(r'<[^>]+>', ' ', html or '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_len]

    def parse_data(self, raw: str) -> str:
        """Converte date italiane e ISO in formato YYYY-MM-DD."""
        if not raw:
            return ''
        raw = raw.strip()

        # ISO 8601
        m = re.match(r'(\d{4}-\d{2}-\d{2})', raw)
        if m:
            return m.group(1)

        # RFC 2822 (RSS): "Thu, 08 May 2026 10:00:00 +0000"
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(raw)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

        # Data italiana: "12 maggio 2026" / "12/05/2026"
        mesi = {
            'gennaio':1,'febbraio':2,'marzo':3,'aprile':4,'maggio':5,'giugno':6,
            'luglio':7,'agosto':8,'settembre':9,'ottobre':10,'novembre':11,'dicembre':12,
            'gen':1,'feb':2,'mar':3,'apr':4,'mag':5,'giu':6,
            'lug':7,'ago':8,'set':9,'ott':10,'nov':11,'dic':12,
        }
        m = re.search(r'(\d{1,2})[/\-\s](\w+)[/\-\s](\d{2,4})', raw)
        if m:
            g, me, a = m.group(1), m.group(2).lower(), m.group(3)
            mese = mesi.get(me) or (int(me) if me.isdigit() else 0)
            anno = int(a) + 2000 if len(a) == 2 else int(a)
            if mese and 1 <= int(g) <= 31:
                try:
                    return datetime(anno, mese, int(g)).strftime('%Y-%m-%d')
                except ValueError:
                    pass
        return ''

    def normalizza_comune(self, raw: str) -> str:
        """Pulisce il nome del comune."""
        c = re.sub(r'\(AV\)|\bAV\b', '', raw or '', flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', c).strip(' ,–-')

    def indovina_categoria(self, testo: str) -> str:
        """Suggerisce la categoria in base alle parole chiave nel testo."""
        tl = (testo or '').lower()
        if re.search(r'sagra|fiera|festa patron', tl):          return 'Sagra'
        if re.search(r'vino|docg|cantina|taurasi|fiano|greco',tl): return 'Enoturismo'
        if re.search(r'concerto|musica|jazz|orchestra',tl):     return 'Musica'
        if re.search(r'mostra|arte|cultura|museo|teatro',tl):   return 'Cultura'
        if re.search(r'sport|gara|corsa|bike|trail',tl):        return 'Sport'
        if re.search(r'san |madonna|patron|processione',tl):    return 'Religioso'
        if re.search(r'gastronomia|cibo|food|ricetta',tl):      return 'Gastronomia'
        if re.search(r'trekking|natura|lago|bosco|oasi',tl):    return 'Natura'
        return self.fonte.get('categoria_default', 'Evento')

    def is_evento(self, testo: str) -> bool:
        """Verifica se il testo descrive un evento."""
        return bool(re.search(
            r'sagra|festival|mostra|fiera|concerto|evento|manifestazione|'
            r'rassegna|convegno|spettacolo|mercato|palio|raduno',
            (testo or '').lower()
        ))
