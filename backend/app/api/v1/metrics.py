from fastapi import APIRouter, Response

from app.services.metrics import render_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", include_in_schema=False)
def get_metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
