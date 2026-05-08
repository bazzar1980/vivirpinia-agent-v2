"""Normalizza gli eventi prima di salvarli nel DB"""
import re
from .config import Config

# Lista comuni AV per validazione
COMUNI_AV = {
    'aiello del sabato','altavilla irpina','andretta','aquilonia','ariano irpino',
    'atripalda','avella','avellino','bagnoli irpino','baiano','bisaccia','bonito',
    'cairano','calabritto','calitri','candida','caposele','capriglia irpina',
    'carife','casalbore','cassano irpino','castel baronia','castelfranci',
    'castelvetere sul calore','cervinara','cesinali','chianche',
    'chiusano di san domenico','contrada','conza della campania','domicella',
    'flumeri','fontanarosa','forino','frigento','gesualdo','greci','grottaminarda',
    'grottolella','guardia lombardi','lacedonia','lapio','lauro','lioni','luogosano',
    'manocalzati','marzano di nola','melito irpino','mercogliano','mirabella eclano',
    'montaguto','montecalvo irpino','montefalcione','monteforte irpino','montefredane',
    'montefusco','montella','montemarano','montemiletto','monteverde','montoro',
    'morra de sanctis','moschiano','mugnano del cardinale','nusco',
    "ospedaletto d'alpinolo",'pago del vallo di lauro','parolise','paternopoli',
    'petruro irpino','pietradefusi','pietrastornina','prata di principato ultra',
    'pratola serra','quadrelle','quindici','rocca san felice','roccabascerana',
    'rotondi','salza irpina','san mango sul calore','san martino valle caudina',
    'san michele di serino','san nicola baronia','san potito ultra','san sossio baronia',
    "sant'andrea di conza","sant'angelo a scala","sant'angelo all'esca",
    "sant'angelo dei lombardi",'santa lucia di serino','santa paolina',
    'santo stefano del sole','savignano irpino','scampitella','senerchia','serino',
    'sirignano','solofra','sorbo serpico','sperone','sturno','summonte','taurano',
    'taurasi','teora','torella dei lombardi','torre le nocelle','torrioni','trevico',
    'tufo','vallata','vallesaccarda','venticano','villamaina','villanova del battista',
    'volturara irpina','zungoli',
    # province/regione
    'avellino','provincia di avellino','irpinia',
}

CATEGORIE_VALIDE = {
    'Sagra','Enoturismo','Cultura','Musica','Sport',
    'Tradizione','Natura','Gastronomia','Religioso','Evento',
}


class Normalizer:

    def normalizza(self, ev: dict) -> dict | None:
        """
        Normalizza un evento grezzo.
        Ritorna None se l'evento non è valido o non riguarda la provincia AV.
        """
        titolo = self._pulisci(ev.get('titolo', ''))
        if not titolo or len(titolo) < 5:
            return None

        comune = self._normalizza_comune(ev.get('comune', ''))

        # Se il comune è specificato, verifica che sia in provincia AV
        if comune and not self._is_av(comune):
            return None

        # Categoria
        cat = ev.get('categoria', 'Evento')
        if cat not in CATEGORIE_VALIDE:
            cat = 'Evento'

        return {
            'titolo':      titolo[:255],
            'data_inizio': self._parse_data(ev.get('data_raw', '') or ev.get('data_inizio', '')),
            'data_fine':   self._parse_data(ev.get('data_fine_raw', '') or ev.get('data_fine', '')),
            'comune':      comune[:120],
            'luogo':       self._pulisci(ev.get('luogo', ''))[:255],
            'categoria':   cat,
            'descrizione': self._pulisci(ev.get('descrizione', ''))[:1000],
            'url_fonte':   (ev.get('url', '') or '')[:500],
            'fonte':       (ev.get('fonte', '') or '')[:120],
            'pubblicato':  1,
        }

    def _pulisci(self, testo: str) -> str:
        import html as html_module
        t = re.sub(r'<[^>]+>', ' ', testo or '')
        t = html_module.unescape(t)
        return re.sub(r'\s+', ' ', t).strip()

    def _normalizza_comune(self, raw: str) -> str:
        c = re.sub(r'\(AV\)|\bAV\b', '', raw or '', flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', c).strip(' ,–-')

    def _is_av(self, comune: str) -> bool:
        return comune.lower() in COMUNI_AV

    def _parse_data(self, raw: str) -> str:
        if not raw:
            return ''
        raw = raw.strip()
        m = re.match(r'(\d{4}-\d{2}-\d{2})', raw)
        if m:
            return m.group(1)
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(raw).strftime('%Y-%m-%d')
        except Exception:
            pass
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
            anno = int(a)+2000 if len(a)==2 else int(a)
            if mese and 1 <= int(g) <= 31:
                try:
                    from datetime import datetime
                    return datetime(anno, mese, int(g)).strftime('%Y-%m-%d')
                except ValueError:
                    pass
        return ''
