from typing import Any

from fastapi import APIRouter, Request

from app.core.security import API_KEY_HEADER


router = APIRouter(tags=["genios-openapi"])


def _json_response(schema_name: str, description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": f"#/components/schemas/{schema_name}"}
            }
        },
    }


def _json_request(schema_name: str) -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": f"#/components/schemas/{schema_name}"}
            }
        },
    }


@router.get("/openapi-genios-runs.json")
def read_genios_runs_openapi(request: Request) -> dict[str, Any]:
    run_id_parameter = {
        "name": "run_id",
        "in": "path",
        "required": True,
        "schema": {"type": "string"},
    }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide Snapshot Review Runs",
            "version": "0.2.0",
            "description": (
                "Prepare a short-lived visit/evidence snapshot, review a sourced draft, "
                "then finalize the exact reviewed answer. Import only after backend "
                "migration and staging validation."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "paths": {
            "/api/genios/runs": {
                "post": {
                    "operationId": "prepare_historyguide_review_run",
                    "summary": "Prepare a review run",
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("PrepareRunRequest"),
                    "responses": {
                        "201": _json_response("PrepareRunResponse", "Run and approved evidence excerpts."),
                        "401": {"description": "Missing or invalid API key."},
                        "404": {"description": "Visitor session was not found."},
                        "422": {"description": "Invalid request."},
                    },
                }
            },
            "/api/genios/runs/{run_id}/review": {
                "post": {
                    "operationId": "review_historyguide_run_draft",
                    "summary": "Review a cited answer draft",
                    "parameters": [run_id_parameter],
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("ReviewRunRequest"),
                    "responses": {
                        "200": _json_response("ReviewRunResponse", "Review decision and safe answer."),
                        "401": {"description": "Missing or invalid API key."},
                        "404": {"description": "Review run was not found."},
                        "409": {"description": "Run expired or source/visitor state changed."},
                        "422": {"description": "Invalid request."},
                    },
                }
            },
            "/api/genios/runs/{run_id}/finalize": {
                "post": {
                    "operationId": "finalize_historyguide_run_answer",
                    "summary": "Release only a reviewed answer",
                    "parameters": [run_id_parameter],
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("FinalizeRunRequest"),
                    "responses": {
                        "200": _json_response("FinalizeRunResponse", "Only answer allowed for display."),
                        "401": {"description": "Missing or invalid API key."},
                        "404": {"description": "Review run was not found."},
                        "409": {"description": "Run unreviewed, revised, stale, expired, or already finalized."},
                        "422": {"description": "Invalid request."},
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": API_KEY_HEADER,
                }
            },
            "schemas": {
                "PrepareRunRequest": {
                    "type": "object",
                    "required": ["session_id"],
                    "properties": {
                        "session_id": {"type": "string"},
                        "recommendation_limit": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
                        "route_max_items": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                    },
                },
                "PrepareRunResponse": {
                    "type": "object",
                    "required": ["run_id", "session_id", "expires_at", "handoff", "approved_evidence"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "session_id": {"type": "string"},
                        "expires_at": {"type": "string", "format": "date-time"},
                        "handoff": {"type": "object"},
                        "approved_evidence": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ApprovedEvidenceExcerpt"},
                        },
                    },
                },
                "ApprovedEvidenceExcerpt": {
                    "type": "object",
                    "required": ["exhibit_id", "source_id", "title", "source_uri", "content_sha256", "excerpt_text", "truncated"],
                    "properties": {
                        "exhibit_id": {"type": "string"},
                        "source_id": {"type": "string"},
                        "title": {"type": "string"},
                        "source_uri": {"type": "string"},
                        "content_sha256": {"type": "string"},
                        "excerpt_text": {"type": "string"},
                        "truncated": {"type": "boolean"},
                    },
                },
                "EvidenceCitation": {
                    "type": "object",
                    "required": ["exhibit_id", "source_id", "evidence_quote"],
                    "properties": {
                        "exhibit_id": {"type": "string"},
                        "source_id": {"type": "string"},
                        "evidence_quote": {"type": "string", "minLength": 8, "maxLength": 800},
                    },
                },
                "ReviewRunRequest": {
                    "type": "object",
                    "required": ["draft_answer", "cited_exhibit_ids"],
                    "properties": {
                        "draft_answer": {"type": "string"},
                        "cited_exhibit_ids": {"type": "string"},
                        "citations": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/EvidenceCitation"},
                        },
                    },
                },
                "ReviewRunResponse": {
                    "type": "object",
                    "required": ["run_id", "session_id", "decision", "issues", "safe_answer", "draft_sha256"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "session_id": {"type": "string"},
                        "decision": {"type": "string", "enum": ["pass", "revise", "block"]},
                        "issues": {"type": "string"},
                        "safe_answer": {"type": "string"},
                        "draft_sha256": {"type": "string"},
                    },
                },
                "FinalizeRunRequest": {
                    "type": "object",
                    "required": ["draft_answer"],
                    "properties": {"draft_answer": {"type": "string"}},
                },
                "FinalizeRunResponse": {
                    "type": "object",
                    "required": ["run_id", "decision", "answer"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "decision": {"type": "string", "enum": ["pass", "block"]},
                        "answer": {"type": "string"},
                    },
                },
            },
        },
    }
