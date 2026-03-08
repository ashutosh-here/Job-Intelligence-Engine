from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.observability.middleware import RequestTelemetryMiddleware
from app.utils.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.add_middleware(RequestTelemetryMiddleware)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "running"}
