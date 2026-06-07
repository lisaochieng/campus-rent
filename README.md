# Campus Rent

Campus Rent is a student housing search project built around a decoupled data pipeline:

1. Scheduled ingestion jobs collect listings from authorized/public listing sources.
2. The backend cleans, deduplicates, scam-checks, scores, and indexes those listings.
3. The app reads from Postgres/OpenSearch so student searches stay fast.

This is the resume-ready architecture: scraping/API collection does not run inside the user search request. The website queries cached, already-cleaned listings.

## Local listing ingestion

Run the stack:

```powershell
docker compose up --build
```

In a second terminal, run a one-school ingestion job:

```powershell
docker compose exec api python -m app.jobs.ingest_listings --school "New York University" --limit 25 --radius-miles 10
```

The job tries configured legal sources in this order:

- `RentCast Rental Listings` when `RENTCAST_API_KEY` is set.
- `Trellistate Public Listings` as a no-key public API with sparse priced inventory.
- `Craigslist Public Rental RSS` as a no-key public feed fallback for supported US markets.

## Hosted database / Supabase

Supabase is PostgreSQL, so the app can use it through `DATABASE_URL`. Add this to `.env` locally or GitHub Actions secrets:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
RENTCAST_API_KEY=your_key_here
SERPAPI_API_KEY=optional_key_here
```

Then the same ingestion job writes into hosted Postgres instead of your local Docker database.

## Scheduled ingestion

The GitHub Actions workflow at `.github/workflows/listing-ingestion.yml` runs every Sunday at 5:00 UTC and can also be triggered manually from GitHub Actions.

Required repository secrets:

- `DATABASE_URL`
- `RENTCAST_API_KEY`

Optional repository secret:

- `SERPAPI_API_KEY`

## Legal sourcing note

Campus Rent should use authorized APIs, public feeds, or sources whose terms permit collection. Avoid bypassing anti-bot systems, Cloudflare protections, or rate limits. That keeps the project credible for deployment and cleaner to discuss in interviews.
