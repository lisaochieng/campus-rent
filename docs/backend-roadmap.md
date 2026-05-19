# Backend Roadmap

## Phase 1: Foundation

- FastAPI service
- Docker Compose local stack
- PostgreSQL/PostGIS, Redis, and OpenSearch services
- Health and readiness endpoints
- Basic tests

## Phase 2: Data Model

- Schools table
- Listings table
- Listing source table
- Listing events table for tracking when data was observed
- Scam signal table for explainable risk scoring
- Alembic migrations for versioned database changes

## Phase 3: Ingestion

- Source adapters with clear boundaries per listing source
- Robots.txt and terms-of-service review per source
- Rate limiting
- Raw listing capture
- Normalization pipeline

## Phase 4: Search

- PostGIS campus-distance queries
- OpenSearch listing index
- Budget, distance, bedroom, freshness, and scam-risk filters
- Redis caching for common searches

## Phase 5: Scoring

- Campus distance score
- Budget fit score
- Source credibility score
- Freshness score
- Scam risk score
- Final CampusRent score

## Phase 6: Production Readiness

- Unit and integration tests
- GitHub Actions
- Structured logging
- Prometheus metrics
- OpenTelemetry tracing
- Kubernetes manifests
- Terraform cloud infrastructure
