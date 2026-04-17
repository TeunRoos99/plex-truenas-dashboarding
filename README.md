# TrueNAS + Plex Dashboard

Lokaal dashboard dat je TrueNAS Scale NAS en Plex Media Server analyseert.
Toont orphaned bestanden, nooit-bekeken content en verouderde items — volledig read-only.

## Vereisten

- Python 3.11+
- TrueNAS Scale met API key (read-only user)
- Plex Media Server met Plex token

---

## Installatie

### 1. Dependencies installeren

```bash
cd truenas-plex-dashboard
pip install -r requirements.txt
```

### 2. .env aanmaken

```bash
cp .env.example .env
```

Vul `.env` in met jouw waarden:

| Variabele | Beschrijving |
|---|---|
| `TRUENAS_URL` | URL naar TrueNAS (bijv. `https://192.168.1.10`) |
| `TRUENAS_API_KEY` | API key van TrueNAS (zie hieronder) |
| `TRUENAS_VERIFY_SSL` | `false` voor self-signed certificaten |
| `PLEX_URL` | URL naar Plex (bijv. `http://192.168.1.10:32400`) |
| `PLEX_TOKEN` | Plex token (zie hieronder) |
| `STALE_MONTHS` | Maanden zonder kijkactiviteit = stale (standaard: 6) |

---

## TrueNAS API Key aanmaken

1. Ga naar TrueNAS UI → **Credentials** → **API Keys**
2. Klik **Add** → geef een naam (bijv. `dashboard-readonly`)
3. Optioneel: maak een read-only user aan en koppel de key daar aan
4. Kopieer de key naar `.env` als `TRUENAS_API_KEY`

---

## Plex Token ophalen

**Via browser:**
1. Open Plex Web → klik op een film/serie → **...** → **Get Info** → **View XML**
2. In de URL zie je `X-Plex-Token=XXXXXXXXXX` — dat is jouw token

**Via curl (als Plex lokaal draait):**
```bash
curl -s "http://localhost:32400/identity" -H "X-Plex-Token: JOUW_TOKEN"
```

**Of via account settings:**
[https://www.plex.tv/claim/](https://www.plex.tv/claim/) of in Plex Web:
Account → **Account** → **Authorized Devices** → XML weergave

---

## Starten

### Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

De API is bereikbaar op `http://localhost:8000`.
Swagger docs: `http://localhost:8000/docs`

### Frontend

Open in je browser:

```bash
open frontend/index.html
```

Of serveer via Python:

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

---

## API Endpoints

| Endpoint | Beschrijving |
|---|---|
| `GET /files` | Alle bestanden op TrueNAS |
| `GET /plex/libraries` | Plex libraries (films + series) |
| `GET /plex/items` | Alle Plex items met metadata |
| `GET /plex/unwatched` | Items nooit bekeken |
| `GET /plex/stale` | Items niet bekeken in 6+ maanden |
| `GET /nas/orphaned` | Mediabestanden op NAS, niet in Plex |
| `GET /summary` | Samenvattende statistieken |
| `DELETE /cache` | Cache wissen (forceer herlaad) |

---

## Projectstructuur

```
truenas-plex-dashboard/
├── backend/
│   ├── main.py       # FastAPI routes + in-memory cache
│   ├── truenas.py    # TrueNAS REST API client
│   ├── plex.py       # Plex API client
│   ├── analyzer.py   # Cross-reference + filteren
│   └── config.py     # .env laden
├── frontend/
│   └── index.html    # React dashboard (CDN, single file)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Opmerkingen

- **Read-only**: het dashboard doet geen schrijfacties op TrueNAS of Plex.
- **Cache**: data wordt gecached per sessie. Klik "Vernieuwen" in de UI om opnieuw te laden.
- **SSL**: zet `TRUENAS_VERIFY_SSL=false` bij self-signed certificaten (gebruikelijk bij TrueNAS thuis).
- **Grote NAS**: recursief bestanden ophalen kan enige tijd duren bij veel datasets.
