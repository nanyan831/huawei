from typing import Any

from fastapi import APIRouter, Request

from app.api.routes.genios_runs_openapi import _json_request, _json_response
from app.core.security import API_KEY_HEADER


router = APIRouter(tags=["genios-openapi"])


@router.get("/openapi-genios-history-runs.json")
def read_genios_history_runs_openapi(request: Request) -> dict[str, Any]:
    run_id_parameter = {
        "name": "run_id", "in": "path", "required": True,
        "schema": {"type": "string"},
    }
    common_errors = {
        "401": {"description": "Missing or invalid API key."},
        "409": {"description": "Unapproved source, stale/expired run, or draft mismatch."},
        "422": {"description": "Invalid request body."},
    }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide General History Review",
            "version": "0.1.0",
            "description": (
                "Exact-excerpt claim and source-attribution checks for history questions "
                "without exhibit IDs. Drafts must consist only of cited literal excerpts. "
                "This service does not independently verify historical truth. "
                "Import only after backend migration and staging validation."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "paths": {
            "/api/genios/history-runs": {
                "post": {
                    "operationId": "prepare_historyguide_history_run",
                    "summary": "Prepare an approved-source history run",
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("HistoryPrepareRequest"),
                    "responses": {
                        "201": _json_response("HistoryPrepareResponse", "Approved source excerpts and run id."),
                        **common_errors,
                    },
                }
            },
            "/api/genios/history-runs/{run_id}/review": {
                "post": {
                    "operationId": "review_historyguide_history_draft",
                    "summary": "Check attributed history draft",
                    "parameters": [run_id_parameter],
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("HistoryReviewRequest"),
                    "responses": {
                        "200": _json_response("HistoryReviewResponse", "Structural citation decision."),
                        "404": {"description": "Run not found."},
                        **common_errors,
                    },
                }
            },
            "/api/genios/history-runs/{run_id}/finalize": {
                "post": {
                    "operationId": "finalize_historyguide_history_answer",
                    "summary": "Release unchanged attributed history answer",
                    "parameters": [run_id_parameter],
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("HistoryFinalizeRequest"),
                    "responses": {
                        "200": _json_response("HistoryFinalizeResponse", "Only answer allowed for display."),
                        "404": {"description": "Run not found."},
                        **common_errors,
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": {"type": "apiKey", "in": "header", "name": API_KEY_HEADER}
            },
            "schemas": {
                "HistoryPrepareRequest": {
                    "type": "object",
                    "required": ["question", "source_ids"],
                    "properties": {
                        "question": {"type": "string"},
                        "source_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10},
                    },
                },
                "HistoryEvidenceExcerpt": {
                    "type": "object",
                    "required": ["source_id", "title", "source_uri", "content_sha256", "excerpt_text", "truncated"],
                    "properties": {
                        "source_id": {"type": "string"},
                        "title": {"type": "string"},
                        "source_uri": {"type": "string"},
                        "content_sha256": {"type": "string"},
                        "excerpt_text": {"type": "string"},
                        "truncated": {"type": "boolean"},
                    },
                },
                "HistoryPrepareResponse": {
                    "type": "object",
                    "required": ["run_id", "expires_at", "approved_evidence"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "expires_at": {"type": "string", "format": "date-time"},
                        "approved_evidence": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/HistoryEvidenceExcerpt"},
                        },
                    },
                },
                "HistoryCitation": {
                    "type": "object",
                    "required": ["source_id", "evidence_quote", "claim_text"],
                    "properties": {
                        "source_id": {"type": "string"},
                        "evidence_quote": {"type": "string", "minLength": 8, "maxLength": 800},
                        "claim_text": {"type": "string", "minLength": 8, "maxLength": 800},
                    },
                },
                "HistoryReviewRequest": {
                    "type": "object",
                    "required": ["draft_answer"],
                    "properties": {
                        "draft_answer": {"type": "string"},
                        "citations": {
                            "type": "array", "items": {"$ref": "#/components/schemas/HistoryCitation"},
                        },
                    },
                },
                "HistoryReviewResponse": {
                    "type": "object",
                    "required": ["run_id", "decision", "issues", "safe_answer", "draft_sha256", "semantic_verified"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "decision": {"type": "string", "enum": ["pass", "revise"]},
                        "issues": {"type": "string"},
                        "safe_answer": {"type": "string"},
                        "draft_sha256": {"type": "string"},
                        "semantic_verified": {"type": "boolean"},
                    },
                },
                "HistoryFinalizeRequest": {
                    "type": "object",
                    "required": ["draft_answer"],
                    "properties": {"draft_answer": {"type": "string"}},
                },
                "HistoryFinalizeResponse": {
                    "type": "object",
                    "required": ["run_id", "answer", "semantic_verified"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "answer": {"type": "string"},
                        "semantic_verified": {"type": "boolean"},
                    },
                },
            },
        },
    }
