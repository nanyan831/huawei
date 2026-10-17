from typing import Any

from fastapi import APIRouter, Request

from app.api.routes.genios_runs_openapi import _json_request, _json_response
from app.core.security import API_KEY_HEADER


router = APIRouter(tags=["genios-openapi"])


@router.get("/openapi-genios-sources.json")
def read_genios_sources_openapi(request: Request) -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NK HistoryGuide Approved Source Search",
            "version": "0.1.0",
            "description": (
                "Bounded literal-keyword lookup over approved backend evidence. "
                "No semantic search or historical-truth verification. "
                "Do not use fixture or unreviewed material for public answers."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "paths": {
            "/api/genios/sources/search": {
                "post": {
                    "operationId": "search_historyguide_approved_sources",
                    "summary": "Find approved source IDs and exact excerpts by keywords",
                    "security": [{"HistoryGuideApiKey": []}],
                    "requestBody": _json_request("ApprovedSourceSearchRequest"),
                    "responses": {
                        "200": _json_response("ApprovedSourceSearchResponse", "Approved literal matches."),
                        "401": {"description": "Missing or invalid business API key."},
                        "422": {"description": "Invalid keyword request."},
                    },
                }
            }
        },
        "components": {
            "securitySchemes": {
                "HistoryGuideApiKey": {"type": "apiKey", "in": "header", "name": API_KEY_HEADER}
            },
            "schemas": {
                "ApprovedSourceSearchRequest": {
                    "type": "object",
                    "required": ["keywords"],
                    "additionalProperties": False,
                    "properties": {
                        "keywords": {
                            "type": "array", "items": {"type": "string", "minLength": 2, "maxLength": 40},
                            "minItems": 1, "maxItems": 5,
                        },
                        "limit": {"type": "integer", "minimum": 1, "maximum": 5, "default": 5},
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
                "ApprovedSourceSearchResponse": {
                    "type": "object",
                    "required": ["retrieval_mode", "matches"],
                    "properties": {
                        "retrieval_mode": {"type": "string", "enum": ["lexical"]},
                        "matches": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/HistoryEvidenceExcerpt"},
                        },
                    },
                },
            },
        },
    }
