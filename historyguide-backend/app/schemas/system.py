from typing import Literal

from pydantic import BaseModel, Field


OperationalAlertSeverity = Literal["warn", "fail"]
OperationalAlertStatus = Literal["ok", "attention_required"]
AccessPolicyLevel = Literal["public", "business_api_key", "operator_api_key", "visitor_token", "local_operator_workflow"]


class OperationalAlert(BaseModel):
    name: str
    severity: OperationalAlertSeverity
    resource_type: str
    count: int = Field(ge=0)
    detail: str


class OperationalAlertsResponse(BaseModel):
    status: OperationalAlertStatus
    total_alerts: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    warn_count: int = Field(ge=0)
    alerts: list[OperationalAlert] = Field(default_factory=list)


class SecurityStatusResponse(BaseModel):
    service: str
    version: str
    business_api_key_configured: bool
    business_api_key_rotation_staged: bool
    operator_api_key_configured: bool
    visitor_gateway_enabled: bool
    business_apis_require_api_key: bool
    operator_apis_require_operator_key: bool
    business_api_key_header: str
    operator_api_key_header: str
    public_probe_paths: list[str]
    operator_paths: list[str]
    operator_path_prefixes: list[str]
    production_note: str


class AccessPolicyEntry(BaseModel):
    name: str
    access_level: AccessPolicyLevel
    required_header: str | None
    paths: list[str] = Field(default_factory=list)
    path_prefixes: list[str] = Field(default_factory=list)
    notes: str


class AccessPolicyResponse(BaseModel):
    service: str
    version: str
    policies: list[AccessPolicyEntry]
    production_note: str
