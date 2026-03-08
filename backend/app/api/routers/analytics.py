from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.engine import AnalyticsEngine
from app.auth.deps import get_current_user, is_admin
from app.db import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_engine = AnalyticsEngine()


@router.get("/overview", response_model=AnalyticsOverview)
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    scope_user = None if is_admin(current_user) else current_user.id
    return analytics_engine.overview(db, user_id=scope_user)


@router.get("/trends")
def analytics_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    scope_user = None if is_admin(current_user) else current_user.id
    return analytics_engine.trends(db, days=days, user_id=scope_user)
