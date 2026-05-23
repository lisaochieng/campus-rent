from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.listings import router as listings_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.schools import router as schools_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(metrics_router)
router.include_router(ingestion_router, prefix="/api/v1")
router.include_router(listings_router, prefix="/api/v1")
router.include_router(schools_router, prefix="/api/v1")
