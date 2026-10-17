from typing import Any

from fastapi import APIRouter, Request

from app.api.routes.genios_runs_openapi import _json_request, _json_response
from app.core.security import API_KEY_HEADER


router = APIRouter(tags=["genios-openapi"])


@router.get("/openapi-genios-answers.json")
def read_genios_answers_openapi(request: Request) -> dict[str, Any]:
    responses = {
        "200": _json_response("ReleasedAnswer", "Only the reviewed final answer or safe block response."),
        "401": {"description": "Missing or invalid business API key."},
        "404": {"description": "Visitor session was not found."},
        "409": {"description": "Draft failed review, evidence changed, or claim support was not approved."},
        "422": {"description": "Invalid request body."},
    }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide Reviewed Answer Release",
            "version": "0.1.0",
            "description": (
                "Single-call backend orchestration of prepare, review and finalize. "
                "The caller must still enforce this tool as its sole visitor answer path. "
                "General history is currently limited to literal approved excerpts."
                " Shared deployments also require an operator-approved claim-to-quote review"
                " for each citation; semantic_verified remains false."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "paths": {
            "/api/genios/answers/history": {
                "post": {
                    "operationId": "release_historyguide_history_answer",
                    "summary": "Release an attributed history answer",
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("HistoryAnswerRequest"),
                    "responses": responses,
                },
            },
            "/api/genios/answers/exhibit": {
                "post": {
                    "operationId": "release_historyguide_exhibit_answer",
                    "summary": "Release a reviewed exhibit or route answer",
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("ExhibitAnswerRequest"),
                    "responses": responses,
                },
            },
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": {"type": "apiKey", "in": "header", "name": API_KEY_HEADER}
            },
            "schemas": {
                "HistoryCitation": {
                    "type": "object", "required": ["source_id", "evidence_quote", "claim_text"],
                    "properties": {
                        "source_id": {"type": "string"},
                        "evidence_quote": {"type": "string", "minLength": 8, "maxLength": 800},
                        "claim_text": {"type": "string", "minLength": 8, "maxLength": 800},
                    },
                },
                "EvidenceCitation": {
                    "type": "object", "required": ["exhibit_id", "source_id", "evidence_quote", "claim_text"],
                    "properties": {
                        "exhibit_id": {"type": "string"},
                        "source_id": {"type": "string"},
                        "evidence_quote": {"type": "string", "minLength": 8, "maxLength": 800},
                        "claim_text": {"type": "string", "minLength": 8, "maxLength": 800},
                    },
                },
                "HistoryAnswerRequest": {
                    "type": "object",
                    "required": ["question", "source_ids", "draft_answer", "citations"],
                    "properties": {
                        "question": {"type": "string", "minLength": 1, "maxLength": 2000},
                        "source_ids": {
                            "type": "array", "items": {"type": "string"},
                            "minItems": 1, "maxItems": 10,
                        },
                        "draft_answer": {"type": "string", "minLength": 1, "maxLength": 8000},
                        "citations": {
                            "type": "array", "items": {"$ref": "#/components/schemas/HistoryCitation"},
                            "minItems": 1, "maxItems": 20,
                        },
                    },
                },
                "ExhibitAnswerRequest": {
                    "type": "object",
                    "required": ["session_id", "draft_answer", "cited_exhibit_ids", "citations"],
                    "properties": {
                        "session_id": {"type": "string", "minLength": 1, "maxLength": 64},
                        "recommendation_limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                        "route_max_items": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                        "draft_answer": {"type": "string", "minLength": 1, "maxLength": 8000},
                        "cited_exhibit_ids": {"type": "string", "minLength": 1, "maxLength": 2000},
                        "citations": {
                            "type": "array", "items": {"$ref": "#/components/schemas/EvidenceCitation"},
                            "minItems": 1, "maxItems": 20,
                        },
                    },
                },
                "ReleasedAnswer": {
                    "type": "object", "required": ["run_id", "decision", "answer", "semantic_verified", "claim_support_reviewed"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "decision": {"type": "string", "enum": ["pass", "block"]},
                        "answer": {"type": "string"},
                        "semantic_verified": {"type": "boolean"},
                        "claim_support_reviewed": {"type": "boolean"},
                    },
                },
            },
        },
    }
