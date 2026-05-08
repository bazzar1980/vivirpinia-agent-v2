"""Scraper per pagine HTML generiche"""
from bs4 import BeautifulSoup
from .base import ScraperBase


class ScraperHTML(ScraperBase):

    def esegui(self) -> list:
        eventi = []
        for url in self.fonte.get('urls', []):
            self.log.info(f"  Fetch: {url}")
            html = self.fetch(url)
            if not html:
                continue
            trovati = self._parse(html, url)
            self.log.info(f"  → {len(trovati)} eventi da {url}")
            eventi.extend(trovati)
        return eventi

    def _parse(self, html: str, url: str) -> list:
        soup = BeautifulSoup(html, 'html.parser')
        eventi = []

        # Selettori CSS comuni per CMS italiani (Joomla, Drupal, custom)
        selettori = [
            'article.evento', 'article.event', 'article.manifestazione',
            'div.views-row', 'div.event-item', 'div.evento',
            'li.evento', 'li.event', 'div.notizia',
            'div.item-manifestazione', 'article',
        ]

        nodi = []
        for sel in selettori:
            nodi = soup.select(sel)
            if nodi:
                break

        if nodi:
            for nodo in nodi[:50]:
                ev = self._estrai_da_nodo(nodo, url)
                if ev:
                    eventi.append(ev)
        else:
            # Fallback: cerca link con parole chiave evento
            for a in soup.find_all('a', href=True):
                testo = a.get_text(strip=True)
                if len(testo) > 10 and self.is_evento(testo):
                    href = a['href']
                    if not href.startswith('http'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + '/' + href.lstrip('/')
                    eventi.append({
                        'titolo':    self.pulisci(testo, 255),
                        'comune':    self._indovina_comune_da_url(url),
                        'url':       href,
                        'categoria': self.indovina_categoria(testo),
                        'fonte':     self.fonte['nome'],
                    })
                    if len(eventi) >= 30:
                        break

        # Filtra per comuni della provincia AV se richiesto
        comuni_filtro = self.fonte.get('comuni_filtro', [])
        if comuni_filtro:
            eventi = [e for e in eventi if
                      not e.get('comune') or
                      any(c.lower() in (e.get('comune') or '').lower() for c in comuni_filtro)]

        return eventi

    def _estrai_da_nodo(self, nodo, url: str) -> dict | None:
        # Titolo
        titolo_tag = (nodo.find(['h2','h3','h4','h5']) or
                      nodo.find('a') or
                      nodo.find(class_=lambda c: c and 'title' in c))
        if not titolo_tag:
            return None
        titolo = self.pulisci(titolo_tag.get_text(), 255)
        if len(titolo) < 5:
            return None

        # Data
        data_tag = (nodo.find('time') or
                    nodo.find(class_=lambda c: c and ('data' in c or 'date' in c)))
        data_raw = ''
        if data_tag:
            data_raw = data_tag.get('datetime', '') or data_tag.get_text(strip=True)

        # Comune/luogo
        luogo_tag = nodo.find(class_=lambda c: c and ('luogo' in c or 'place' in c or 'comune' in c or 'location' in c))
        luogo = self.pulisci(luogo_tag.get_text(), 120) if luogo_tag else ''

        # Link
        a = nodo.find('a', href=True)
        href = ''
        if a:
            href = a['href']
            if not href.startswith('http'):
                base = '/'.join(url.split('/')[:3])
                href = base + '/' + href.lstrip('/')

        # Descrizione
        p = nodo.find('p')
        desc = self.pulisci(p.get_text(), 500) if p else ''

        return {
            'titolo':    titolo,
            'data_raw':  data_raw,
            'comune':    self.normalizza_comune(luogo) or self._indovina_comune_da_url(url),
            'luogo':     luogo,
            'descrizione': desc,
            'url':       href or url,
            'categoria': self.indovina_categoria(titolo + ' ' + desc),
            'fonte':     self.fonte['nome'],
        }

    def _indovina_comune_da_url(self, url: str) -> str:
        """Prova a ricavare il comune dall'URL (es. comune.nusco.av.it)."""
        import re
        m = re.search(r'comune\.([^.]+)\.av\.it', url)
        if m:
            return m.group(1).replace('-', ' ').title()
        return ''
