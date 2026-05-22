# CampusRent

CampusRent is a backend-first rental discovery platform for students. The app will collect rental listings from credible permitted sources, clean and deduplicate them, score listings by campus distance, affordability, freshness, and scam risk, then serve fast search results through a cloud-ready API.

## Why This Project Is Resume-Strong

This project is designed to show practical backend and cloud infrastructure skills:

- FastAPI service design
- PostgreSQL data modeling
- PostGIS geospatial search
- OpenSearch indexing
- Redis caching
- Docker-based local development
- Background ingestion workers
- Data cleaning and scam-risk scoring
- CI/CD, observability, Kubernetes, and cloud deployment in later phases

## Current Phase

Phase 1 builds the backend foundation:

- FastAPI API service
- Environment-based configuration
- Dockerfile
- Docker Compose with API, PostgreSQL, Redis, and OpenSearch
- Health and readiness endpoints
- Basic test structure

## Local Development

### Prerequisites

Install:

- Git
- Docker Desktop
- Python 3.12+
- VS Code

Recommended VS Code extensions:

- Python
- Pylance
- Docker
- GitHub Pull Requests
- YAML
- Kubernetes
- Terraform

### Python Virtual Environment

From the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements-dev.txt
```

### Run With Docker

```powershell
docker compose up --build
```

API docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

Readiness check:

```text
http://localhost:8000/ready
```

Schools endpoint after migrations and seed data:

```text
http://localhost:8000/api/v1/schools
```

Listings endpoint after seed data:

```text
http://localhost:8000/api/v1/listings
http://localhost:8000/api/v1/listings?city=New%20York&max_rent=3000
```

School-based ranked search:

```text
http://localhost:8000/api/v1/listings/search?school_id=SCHOOL_ID&max_rent=3000
```

Use `/api/v1/schools` to get a valid `SCHOOL_ID`.

Ranked search includes explainable scoring fields:

- Distance from the selected school
- Budget fit
- Listing freshness placeholder
- Scam safety score
- Scam signal explanations when suspicious patterns are detected

### Database Migrations

Database tables are managed with Alembic. A migration is a versioned database change that can be reviewed, committed, and replayed in every environment.

After the Docker services are running, open a second terminal and run:

```powershell
docker compose exec api alembic -c alembic.ini upgrade head
```

That command applies all pending migrations to PostgreSQL.

To add starter data for local development:

```powershell
docker compose exec api python -m app.db.seed
```

Seed data is intentionally small and safe. It gives the backend known schools and a trusted manual listing source before the ingestion system exists.

When models change later, create a new migration:

```powershell
docker compose exec api alembic -c alembic.ini revision --autogenerate -m "describe the schema change"
docker compose exec api alembic -c alembic.ini upgrade head
```

The first command creates a migration file from model changes. The second command applies it.

## Git Workflow

Your first commit:

```powershell
git add .
git commit -m "Initialize CampusRent backend foundation"
git push -u origin main
```

For future work:

```powershell
git checkout -b feature/database-schema
```

Then:

```powershell
git add .
git commit -m "Add initial database schema"
git push origin feature/database-schema
```

Open a pull request on GitHub, even when working solo. It creates a professional history of design decisions, checks, and incremental progress.

## Roadmap

1. Backend foundation
2. Database schema and migrations
3. Listing ingestion pipeline
4. Data cleaning and normalization
5. Campus distance scoring with PostGIS
6. Fast listing search with OpenSearch
7. Redis caching
8. Scam-risk scoring
9. Tests and GitHub Actions
10. Observability with metrics, logs, and traces
11. Kubernetes deployment
12. Cloud infrastructure with Terraform
