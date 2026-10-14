from typing import Any

from fastapi import APIRouter, Request


router = APIRouter(tags=["genios-openapi"])


def _historyguide_api_key_security_scheme() -> dict[str, str]:
    return {
        "type": "apiKey",
        "in": "header",
        "name": "X-HistoryGuide-Api-Key",
    }


@router.get("/openapi-genios-handoff.json")
def read_genios_handoff_openapi(request: Request) -> dict[str, Any]:
    base_url = str(request.base_url).rstrip("/")
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide GeniOS Handoff Plugin",
            "description": (
                "Expose the NK HistoryGuide backend handoff package for GeniOS. "
                "The backend returns structured visitor context, route hints, "
                "visit summary, and source-safety signals; it does not generate "
                "museum explanation text."
            ),
            "version": "0.1.0",
        },
        "servers": [
            {
                "url": base_url,
                "description": "NK HistoryGuide backend base URL",
            }
        ],
        "paths": {
            "/api/genios/handoff/{session_id}": {
                "get": {
                    "operationId": "get_genios_handoff",
                    "summary": "Get GeniOS handoff package",
                    "description": (
                        "Return structured handoff data for one museum visit session. "
                        "GeniOS should generate explanation content only when "
                        "source_safety.ready_for_generation is true."
                    ),
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "description": "Visitor session id for one real museum visit.",
                            "schema": {
                                "type": "string",
                                "example": "demo-session-001",
                            },
                        },
                        {
                            "name": "recommendation_limit",
                            "in": "query",
                            "required": False,
                            "description": "Maximum recommendation candidates to include.",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "default": 3,
                            },
                        },
                        {
                            "name": "route_max_items",
                            "in": "query",
                            "required": False,
                            "description": "Maximum route plan items to include.",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "default": 5,
                            },
                        },
                    ],
                    "security": [
                        {
                            "HistoryGuideApiKey": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Structured handoff package for GeniOS.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/GeniosHandoff"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid API key."
                        },
                        "404": {
                            "description": "Visitor session was not found."
                        },
                        "422": {
                            "description": "Invalid request parameters."
                        },
                    },
                }
            }
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": {
                    **_historyguide_api_key_security_scheme(),
                }
            },
            "schemas": {
                "GeniosHandoff": {
                    "type": "object",
                    "required": [
                        "session_id",
                        "source_safety",
                        "preflight",
                        "context",
                        "route_plan",
                        "visit_summary",
                        "handoff_note",
                    ],
                    "properties": {
                        "session_id": {
                            "type": "string"
                        },
                        "source_safety": {
                            "$ref": "#/components/schemas/SourceSafety"
                        },
                        "preflight": {
                            "type": "object",
                            "description": "Structured readiness checks before GeniOS generation.",
                        },
                        "context": {
                            "type": "object",
                            "description": (
                                "Visitor State, exhibit context, visit events, "
                                "recommendations, and grounding exhibit ids."
                            ),
                        },
                        "route_plan": {
                            "type": "object",
                            "description": "Rule-based route plan for the remaining visit.",
                        },
                        "visit_summary": {
                            "type": "object",
                            "description": "Structured visit summary for recap and continuity.",
                        },
                        "handoff_note": {
                            "type": "string"
                        },
                    },
                },
                "SourceSafety": {
                    "type": "object",
                    "required": [
                        "ready_for_generation",
                        "grounding_sources_complete",
                        "source_reference_count",
                        "sourced_exhibit_ids",
                        "unsourced_exhibit_ids",
                        "missing_exhibit_ids",
                        "blocking_check_names",
                        "safety_note",
                    ],
                    "properties": {
                        "ready_for_generation": {
                            "type": "boolean",
                            "description": (
                                "GeniOS may generate explanation content only when "
                                "this value is true."
                            ),
                        },
                        "grounding_sources_complete": {
                            "type": "boolean"
                        },
                        "source_reference_count": {
                            "type": "integer"
                        },
                        "sourced_exhibit_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                        },
                        "unsourced_exhibit_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                        },
                        "missing_exhibit_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                        },
                        "blocking_check_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                        },
                        "safety_note": {
                            "type": "string"
                        },
                    },
                },
            },
        },
    }


@router.get("/openapi-genios-review.json")
def read_genios_review_openapi(request: Request) -> dict[str, Any]:
    base_url = str(request.base_url).rstrip("/")
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide Answer Review",
            "description": (
                "Deterministically review one museum-answer draft against HistoryGuide "
                "source safety, exhibit references, fixture detection, and route order."
            ),
            "version": "0.1.0",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/genios/review": {
                "post": {
                    "operationId": "review_genios_answer",
                    "summary": "Review a GeniOS answer draft",
                    "description": (
                        "Return pass, revise, or block using deterministic backend checks. "
                        "This tool does not call a large language model."
                    ),
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ReviewRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Flat deterministic review result.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ReviewResponse"}
                                }
                            },
                        },
                        "401": {"description": "Missing or invalid API key."},
                        "404": {"description": "Visitor session was not found."},
                        "422": {"description": "Invalid request body."},
                    },
                }
            }
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": _historyguide_api_key_security_scheme()
            },
            "schemas": {
                "ReviewRequest": {
                    "type": "object",
                    "required": ["session_id", "draft_answer", "cited_exhibit_ids"],
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "default": "demo-session-001",
                            "description": "Visitor session id.",
                        },
                        "draft_answer": {
                            "type": "string",
                            "description": "Answer draft produced by the main Agent.",
                        },
                        "cited_exhibit_ids": {
                            "type": "string",
                            "description": "Comma-separated exhibit ids cited in draft order.",
                        },
                        "recommendation_limit": {
                            "type": "integer",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "route_max_items": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10,
                        },
                    },
                },
                "ReviewResponse": {
                    "type": "object",
                    "required": [
                        "session_id",
                        "decision",
                        "issues",
                        "safe_answer",
                        "ready_for_generation",
                        "grounding_sources_complete",
                        "route_order_valid",
                        "exhibit_ids_valid",
                        "source_references_valid",
                        "fixture_data_detected",
                        "checked_exhibit_ids",
                    ],
                    "properties": {
                        "session_id": {"type": "string"},
                        "decision": {
                            "type": "string",
                            "enum": ["pass", "revise", "block"],
                        },
                        "issues": {"type": "string"},
                        "safe_answer": {"type": "string"},
                        "ready_for_generation": {"type": "boolean"},
                        "grounding_sources_complete": {"type": "boolean"},
                        "route_order_valid": {"type": "boolean"},
                        "exhibit_ids_valid": {"type": "boolean"},
                        "source_references_valid": {"type": "boolean"},
                        "fixture_data_detected": {"type": "boolean"},
                        "checked_exhibit_ids": {"type": "string"},
                    },
                },
            },
        },
    }
