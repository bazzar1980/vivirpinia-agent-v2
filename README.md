# VivIrpinia Scraping Agent

Agente di scraping automatico per il portale VivIrpinia.
Raccoglie eventi e manifestazioni da fonti web e li salva nel database WordPress.

## Struttura

```
agente/
├── agent.py              # Orchestratore principale
├── fonti.yaml            # ← QUI aggiungi/rimuovi le fonti
├── requirements.txt
├── .env.example          # Copia in .env e compila
├── core/
│   ├── config.py         # Configurazione da variabili d'ambiente
│   ├── normalizer.py     # Normalizza e valida i dati
│   └── wp_writer.py      # Salva nel DB WordPress via REST API
├── scrapers/
│   ├── base.py           # Classe base con metodi comuni
│   ├── scraper_html.py   # Scraper pagine HTML generiche
│   ├── scraper_rss.py    # Scraper feed RSS/Atom
│   └── scraper_facebook.py # Scraper Facebook Graph API
└── .github/
    └── workflows/
        └── scraping.yml  # GitHub Actions (automatico)
```

## Configurazione

### 1. Variabili d'ambiente

Copia `.env.example` in `.env` e compila:

```bash
cp .env.example .env
```

Valori necessari:
- `WP_URL` — URL del sito WordPress (es. `https://www.vivirpinia.it`)
- `WP_USER` — nome utente admin WordPress
- `WP_APP_PASSWORD` — Application Password (WP Admin → Utenti → Profilo → Application Passwords)
- `FB_TOKEN` — token Facebook (opzionale, per le fonti Facebook)

### 2. GitHub Secrets

Su GitHub → Settings → Secrets → Actions, aggiungi:
- `WP_URL`
- `WP_USER`
- `WP_APP_PASSWORD`
- `FB_TOKEN` (opzionale)

## Aggiungere/rimuovere fonti

**Tutto si gestisce nel file `fonti.yaml`** — non serve toccare il codice.

### Aggiungere una fonte HTML:
```yaml
- id: mio_sito
  nome: Nome del sito
  tipo: html
  enabled: true
  urls:
    - https://www.esempio.it/eventi/
  categoria_default: Sagra
```

### Aggiungere un feed RSS:
```yaml
- id: mio_rss
  nome: Feed RSS
  tipo: rss
  enabled: true
  urls:
    - https://www.esempio.it/feed/
  categoria_default: Cultura
```

### Disabilitare temporaneamente una fonte:
```yaml
- id: sagre_it
  enabled: false   # ← cambia da true a false
  ...
```

## Uso manuale

```bash
# Installa dipendenze
pip install -r requirements.txt

# Scraping completo (tutte le fonti)
python agent.py

# Solo una fonte specifica
python agent.py --fonte sagre_it

# Dry run — mostra cosa troverebbe senza salvare
python agent.py --dry-run

# Elenca le fonti configurate
python agent.py --lista-fonti

# Dry run su una fonte specifica
python agent.py --fonte provincia_avellino --dry-run
```

## GitHub Actions

Lo scraping viene eseguito automaticamente 4 volte al giorno (6, 12, 18, 22 UTC).

Per avviarlo manualmente: GitHub → Actions → VivIrpinia Scraping → Run workflow.
Puoi specificare una fonte specifica o attivare il dry run.

I log vengono salvati come artifact per 7 giorni.
