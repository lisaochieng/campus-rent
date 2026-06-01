from fastapi import APIRouter

from app.api.v1.data_sources import router as data_sources_router
from app.api.v1.health import router as health_router
from app.api.v1.housing_leads import router as housing_leads_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.listing_reports import router as listing_reports_router
from app.api.v1.listings import router as listings_router
from app.api.v1.market import router as market_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.saved_listings import router as saved_listings_router
from app.api.v1.schools import router as schools_router
from app.api.v1.scraper_runs import router as scraper_runs_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(metrics_router)
router.include_router(data_sources_router, prefix="/api/v1")
router.include_router(housing_leads_router, prefix="/api/v1")
router.include_router(ingestion_router, prefix="/api/v1")
router.include_router(listing_reports_router, prefix="/api/v1")
router.include_router(listings_router, prefix="/api/v1")
router.include_router(market_router, prefix="/api/v1")
router.include_router(saved_listings_router, prefix="/api/v1")
router.include_router(schools_router, prefix="/api/v1")
router.include_router(scraper_runs_router, prefix="/api/v1")
