from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SourceCreate(BaseModel):
    url: HttpUrl
    type: str
    refresh_interval: int = Field(default=3600, ge=300)
    keywords: list[str] | None = None
    custom_selectors: dict[str, str] | None = None


class SourceRead(BaseModel):
    id: int
    user_id: int
    url: str
    type: str
    refresh_interval: int
    status: str
    last_run_at: datetime | None
    keywords: list[str] | None
    custom_selectors: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
