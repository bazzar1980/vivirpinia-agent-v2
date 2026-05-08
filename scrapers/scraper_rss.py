"""Scraper per feed RSS/Atom"""
import xml.etree.ElementTree as ET
from .base import ScraperBase


class ScraperRSS(ScraperBase):

    def esegui(self) -> list:
        eventi = []
        for url in self.fonte.get('urls', []):
            self.log.info(f"  RSS: {url}")
            xml = self.fetch(url)
            if not xml:
                continue
            trovati = self._parse(xml, url)
            self.log.info(f"  → {len(trovati)} eventi da {url}")
            eventi.extend(trovati)
        return eventi

    def _parse(self, xml_text: str, url: str) -> list:
        eventi = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            self.log.warning(f"XML non valido: {e}")
            return []

        ns = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc':      'http://purl.org/dc/elements/1.1/',
            'atom':    'http://www.w3.org/2005/Atom',
        }

        # Supporta sia RSS 2.0 che Atom
        items = root.findall('.//item') or root.findall('.//atom:entry', ns)

        for item in items:
            titolo = self._text(item, ['title'])
            if not titolo:
                continue

            # Filtra: solo voci che sembrano eventi
            desc_tag = (self._text(item, ['description']) or
                        self._text(item, ['content:encoded'], ns) or
                        self._text(item, ['summary']) or '')

            if not self.is_evento(titolo + ' ' + desc_tag):
                continue

            data_raw = (self._text(item, ['pubDate']) or
                        self._text(item, ['dc:date'], ns) or
                        self._text(item, ['updated']) or '')

            link = (self._text(item, ['link']) or
                    item.find('atom:link', ns) and item.find('atom:link', ns).get('href', '') or url)

            # Cerca comune nel testo
            comune = self._indovina_comune_da_url(url)

            eventi.append({
                'titolo':      self.pulisci(titolo, 255),
                'data_raw':    data_raw,
                'comune':      comune,
                'descrizione': self.pulisci(desc_tag, 500),
                'url':         link or url,
                'categoria':   self.indovina_categoria(titolo + ' ' + desc_tag),
                'fonte':       self.fonte['nome'],
            })

        return eventi

    def _text(self, element, tags: list, ns: dict = None) -> str:
        for tag in tags:
            child = element.find(tag, ns) if ns else element.find(tag)
            if child is not None and child.text:
                return child.text.strip()
        return ''

    def _indovina_comune_da_url(self, url: str) -> str:
        import re
        m = re.search(r'comune\.([^.]+)\.av\.it', url)
        if m:
            return m.group(1).replace('-', ' ').title()
        return ''
