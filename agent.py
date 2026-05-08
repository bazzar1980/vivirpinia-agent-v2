#!/usr/bin/env python3
"""
VivIrpinia Scraping Agent
=========================
Legge le fonti da fonti.yaml, esegue lo scraping e salva i risultati
nel database WordPress via REST API.

Uso:
    python agent.py                    # scraping completo
    python agent.py --fonte sagre_it   # solo una fonte
    python agent.py --dry-run          # mostra cosa troverebbe senza salvare
    python agent.py --lista-fonti      # elenca le fonti configurate
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import yaml

from core.config import Config
from core.normalizer import Normalizer
from core.wp_writer import WPWriter
from scrapers.scraper_html import ScraperHTML
from scrapers.scraper_rss import ScraperRSS
from scrapers.scraper_facebook import ScraperFacebook

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraping.log', encoding='utf-8'),
    ]
)
log = logging.getLogger('agent')


def carica_fonti(path: str = 'fonti.yaml') -> list:
    """Carica e valida le fonti dal file YAML."""
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    fonti = data.get('fonti', [])
    # Filtra solo quelle abilitate
    return [f for f in fonti if f.get('enabled', True)]


def crea_scraper(fonte: dict, config: 'Config'):
    """Restituisce lo scraper corretto in base al tipo della fonte."""
    tipo = fonte.get('tipo', 'html').lower()
    if tipo == 'rss':
        return ScraperRSS(fonte, config)
    elif tipo == 'facebook':
        return ScraperFacebook(fonte, config)
    else:
        return ScraperHTML(fonte, config)


def main():
    parser = argparse.ArgumentParser(description='VivIrpinia Scraping Agent')
    parser.add_argument('--fonte',       help='Esegui solo questa fonte (id)')
    parser.add_argument('--dry-run',     action='store_true', help='Non salvare, solo mostra')
    parser.add_argument('--lista-fonti', action='store_true', help='Elenca le fonti configurate')
    parser.add_argument('--fonti-file',  default='fonti.yaml', help='Path del file fonti (default: fonti.yaml)')
    args = parser.parse_args()

    config    = Config()
    normalizer = Normalizer()
    writer    = WPWriter(config) if not args.dry_run else None

    # ── Lista fonti ───────────────────────────────────────────
    fonti = carica_fonti(args.fonti_file)

    if args.lista_fonti:
        print(f"\nFonti configurate ({len(fonti)}):\n")
        for f in fonti:
            stato = '✅' if f.get('enabled', True) else '⏸'
            print(f"  {stato} [{f['id']}] {f['nome']} ({f['tipo']})")
        print()
        return

    # ── Filtra per fonte specifica ────────────────────────────
    if args.fonte:
        fonti = [f for f in fonti if f['id'] == args.fonte]
        if not fonti:
            log.error(f"Fonte '{args.fonte}' non trovata o non abilitata in fonti.yaml")
            sys.exit(1)

    log.info(f"Avvio scraping — {len(fonti)} fonti da processare")
    if args.dry_run:
        log.info("DRY RUN — nessun dato verrà salvato")

    totale_trovati = 0
    totale_salvati = 0
    errori         = []

    for fonte in fonti:
        log.info(f"── Fonte: {fonte['nome']} ({fonte['tipo']}) ──")
        try:
            scraper = crea_scraper(fonte, config)
            eventi  = scraper.esegui()

            if not eventi:
                log.info(f"  Nessun evento trovato")
                continue

            log.info(f"  Trovati: {len(eventi)}")
            totale_trovati += len(eventi)

            # Normalizza
            eventi_norm = [normalizer.normalizza(e) for e in eventi]
            eventi_norm = [e for e in eventi_norm if e]  # rimuovi None

            if args.dry_run:
                for e in eventi_norm:
                    print(f"    → {e.get('titolo', '?')} | {e.get('data_inizio', '?')} | {e.get('comune', '?')}")
            else:
                salvati = writer.salva_eventi(eventi_norm)
                log.info(f"  Salvati: {salvati} nuovi")
                totale_salvati += salvati

        except Exception as ex:
            log.error(f"  ERRORE {fonte['nome']}: {ex}")
            errori.append({'fonte': fonte['nome'], 'errore': str(ex)})

        time.sleep(2)  # pausa tra una fonte e l'altra

    # ── Riepilogo ─────────────────────────────────────────────
    log.info(f"\n{'='*50}")
    log.info(f"RIEPILOGO SCRAPING")
    log.info(f"  Fonti processate : {len(fonti)}")
    log.info(f"  Eventi trovati   : {totale_trovati}")
    if not args.dry_run:
        log.info(f"  Nuovi salvati    : {totale_salvati}")
    log.info(f"  Errori           : {len(errori)}")
    if errori:
        for e in errori:
            log.warning(f"  ⚠ {e['fonte']}: {e['errore']}")
    log.info(f"{'='*50}")


if __name__ == '__main__':
    main()
