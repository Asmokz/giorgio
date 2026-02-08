# Giorgio 🇮🇹

Un bot passionné de cinéma qui track tes visionnages Jellyfin et te demande de noter ce que tu regardes.

## Features

- 🎬 Détecte automatiquement quand tu finis un film/épisode
- ⭐ Demande une note de 1 à 10 via Discord
- 📊 Statistiques de visionnage
- 🔄 Synchronisation automatique du catalogue Jellyfin

## Installation

1. Clone le repo
2. Copie `.env.example` vers `.env` et remplis les valeurs
3. Lance avec Docker :
```bash
docker-compose up -d
```

## Configuration Jellyfin

1. Installe le plugin **Webhook**
2. Configure un webhook vers `http://giorgio:5555/api/webhook`
3. Active l'événement `PlaybackStop`

## API Endpoints

- `GET /health` — Health check
- `GET /api/stats/` — Statistiques globales
- `GET /api/stats/most-watched` — Top contenus vus
- `GET /api/stats/top-rated` — Top contenus notés
- `GET /api/stats/user/{id}` — Stats utilisateur

## Tech Stack

- FastAPI
- Discord.py
- SQLAlchemy + MariaDB
- Docker
```

---

**Structure finale du projet :**
```
giorgio/
├── docker-compose.yml
├── Dockerfile
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── alembic.ini
├── config/
│   └── settings.py
└── src/
    ├── __init__.py
    ├── main.py
    ├── api/
    │   ├── __init__.py
    │   ├── webhooks.py
    │   └── stats.py
    ├── bot/
    │   ├── __init__.py
    │   └── discord_bot.py
    ├── models/
    │   ├── __init__.py
    │   └── database.py
    ├── schemas/
    │   ├── __init__.py
    │   └── jellyfin.py
    └── services/
        ├── __init__.py
        ├── database_service.py
        ├── jellyfin_sync.py
        └── stats_service.py