from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: str
    actor: str
    details: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogCountItem(BaseModel):
    value: str
    count: int = Field(ge=1)


class AuditLogStats(BaseModel):
    total_logs: int = Field(ge=0)
    actions: list[AuditLogCountItem] = Field(default_factory=list)
    resource_types: list[AuditLogCountItem] = Field(default_factory=list)
    actors: list[AuditLogCountItem] = Field(default_factory=list)
    latest_created_at: datetime | None = None
