# DevNews

A public, no-auth, read-only developer news aggregator dashboard. DevNews scrapes tech news, security advisories, hackathons, open source programs, and developer events from multiple sources, deduplicates and groups related stories, and presents them as an infinite-scroll card feed with filters and search.

## Features
- **No Auth:** Read-only access for everyone.
- **Aggregated content:** Security, AI, Open Source, and Events aggregated into grouped stories.
- **Infinite scroll:** Effortless browsing.
- **Shortcuts:** Fast keyboard navigation (j/k, /).

## Tech Stack
**Frontend:** React 18, TypeScript, Tailwind CSS, Zustand, Vite (Deployed on Vercel)
**Backend:** Python 3.11, FastAPI, APScheduler, feedparser, requests, sentence-transformers, slowapi (Deployed on Render)
**Database:** Turso (libSQL hosted SQLite) with FTS5 and WAL mode enabled
**Heavy Scraping:** Playwright running via GitHub Actions

## Setup Instructions

### Backend (Local Development)
1. Navigate to the project root.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install -r backend/requirements.txt`
5. Create a `.env` file based on `.env.example`.
6. Run the server: `python -m uvicorn backend.main:app --reload`

### Frontend (Local Development)
1. Navigate to the `frontend` folder.
2. Install dependencies: `npm install`
3. Copy `.env.example` to `.env.local` if needed and update the backend URL.
4. Start the dev server: `npm run dev`

### Scraping (Local Playwright)
1. Install playwright dependencies: `pip install -r scrapers/requirements-playwright.txt`
2. Install chromium: `playwright install chromium`
3. Set `API_URL` and `API_KEY` environment variables.
4. Run scraper: `python scrapers/playwright_scraper.py`

## Environment Variables
See `.env.example` for details. You need:
- `DATABASE_URL` and `DATABASE_AUTH_TOKEN` from Turso configuration.
- `API_KEY` a secret token for the ingest webhook.
- `ALLOWED_ORIGINS` for CORS.

## Deploying
- **Backend**: Connect your repo to Render, use the provided Dockerfile inside the backend directory. Add a health check ping to your `/healthz` endpoint via UptimeRobot to prevent cold boots if you wish.
- **Frontend**: Connect your repo to Vercel, setting the Root Directory to `frontend`.
- **Database**: Create a database in Turso, grab the connection string and auth token.
- **GitHub Actions**: Add `API_URL` and `API_KEY` to your repository secrets to enable the scheduled Playwright scraper.

## Adding a Source
Open the `sources.yaml` file in the project root and add your source following the existing format. Give it a unique name and define its fetch interval. Restart the backend to begin scraping.
