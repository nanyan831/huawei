from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_web_h5_genios_integration_document_is_linked_from_readme() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/web_h5_genios_integration.md" in readme
    assert "docs/web_h5_integration_checklist.md" in readme
    assert "docs/genios_handoff_evidence_template.md" in readme
    assert "docs/backup_rollback_drill.md" in readme
    assert "docs/operator_runbook.md" in readme
    assert "docs/real_exhibit_seed_review.md" in readme
    assert "docs/production_hardening.md" in readme
    assert "docs/database_migrations.md" in readme
    assert "docs/centralized_logging.md" in readme
    assert "docs/monitoring_alert_examples.md" in readme
    assert "docs/operator_evidence_package_checklist.md" in readme
    assert "docs/production_readiness_decision_checklist.md" in readme
    assert "docs/staging_validation_record.md" in readme
    assert "docs/real_data_import_runbook.md" in readme
    assert "docs/real_data_preimport_final_checklist.md" in readme
    assert "scripts\\deployment_self_check.py" in readme
    assert "scripts\\verify_exhibit_backup.py" in readme
    assert "scripts\\rehearse_exhibit_restore.py" in readme
    assert "scripts\\rehearse_migrations.py" in readme
    assert "scripts\\validate_backend_readiness.py" in readme
    assert "scripts\\validate_staging_database.py" in readme
    assert "scripts\\validate_runtime_config.py" in readme


def test_web_h5_genios_integration_document_covers_real_visit_flow() -> None:
    document = (PROJECT_ROOT / "docs" / "web_h5_genios_integration.md").read_text(encoding="utf-8")

    required_terms = [
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "GET /api/visits/{session_id}/summary",
        "source_safety.ready_for_generation",
        "X-HistoryGuide-Api-Key",
        "X-HistoryGuide-Request-Id",
        "does not generate",
        "digital human, AR, VR",
    ]

    for term in required_terms:
        assert term in document


def test_web_h5_integration_checklist_covers_acceptance_gates() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "docs" / "web_h5_integration_checklist.md").read_text(
        encoding="utf-8"
    )

    required_terms = [
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "X-HistoryGuide-Api-Key",
        "X-HistoryGuide-Operator-Key",
        "X-HistoryGuide-Request-Id",
        "GET /health",
        "GET /ready",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/exhibits/source-report",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "source_safety.ready_for_generation=true",
        "grounding_sources_complete=true",
        "Stop Conditions",
    ]

    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not run RAG",
        "does not generate explanation content",
        "digital human",
        "AR/VR",
        "GeniOS remains responsible",
        "frontend page implementation",
    ]
    for term in boundary_terms:
        assert term in checklist

    assert "docs/web_h5_integration_checklist.md" in readme
    assert "docs/web_h5_integration_checklist.md" in readiness
    assert "docs/web_h5_integration_checklist.md" in handoff


def test_genios_handoff_evidence_template_covers_integration_evidence() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(encoding="utf-8")
    template = (PROJECT_ROOT / "docs" / "genios_handoff_evidence_template.md").read_text(
        encoding="utf-8"
    )
    example = (
        PROJECT_ROOT / "docs" / "examples" / "genios_handoff_evidence.example.md"
    ).read_text(encoding="utf-8")

    required_terms = [
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "POST /api/visitor-states/{session_id}/visit-events",
        "X-HistoryGuide-Request-Id",
        "grounding_sources_complete=true",
        "source_safety.ready_for_generation=true",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "Pass Criteria",
        "Stop Conditions",
    ]

    for term in required_terms:
        assert term in template

    boundary_terms = [
        "does not define a GeniOS prompt",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "digital human or AR/VR",
        "proof of historical accuracy",
        "visitor identity",
        "visitor profile data",
    ]
    for term in boundary_terms:
        assert term in template

    for document in (readme, readiness, handoff, staging_record):
        assert "docs/genios_handoff_evidence_template.md" in document

    for document in (readme, readiness, staging_record, template):
        assert "docs/examples/genios_handoff_evidence.example.md" in document

    example_terms = [
        "placeholder values only",
        "not evidence that GeniOS handoff has been validated",
        "fixture-exhibit-001",
        "example-request-205",
        "`grounding_sources_complete=true`: yes",
        "`source_safety.ready_for_generation=true`: yes",
        "does not define a GeniOS prompt",
        "does not run RAG",
        "does not generate explanation content",
    ]
    for term in example_terms:
        assert term in example


def test_real_exhibit_seed_review_document_covers_import_safety_gates() -> None:
    document = (PROJECT_ROOT / "docs" / "real_exhibit_seed_review.md").read_text(encoding="utf-8")

    required_terms = [
        "source_reference",
        "python scripts\\import_exhibits.py --dry-run",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "GET /api/exhibits/source-report",
        "GET /api/exhibits/quality-report",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "source_safety.ready_for_generation",
        "does not create, infer, rewrite, or generate historical facts",
        "do not import",
    ]

    for term in required_terms:
        assert term in document


def test_real_data_import_runbook_covers_end_to_end_gates() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "real_data_import_runbook.md").read_text(encoding="utf-8")

    required_terms = [
        "Manual Source Review",
        "Runtime Config Gate",
        "Migration Gate",
        "Backup Gate",
        "Seed Dry-Run Gate",
        "Import Gate",
        "Post-Import Backend Checks",
        "GeniOS Handoff Checks",
        "source_safety.ready_for_generation",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\import_exhibits.py --dry-run",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "GET /api/exhibits/source-report",
        "GET /api/genios/handoff/{session_id}",
        "X-HistoryGuide-Request-Id",
        "Stop Conditions",
    ]

    for term in required_terms:
        assert term in runbook

    boundary_terms = [
        "does not create, infer, rewrite, or generate historical facts",
        "does not replace museum or expert review",
        "does not train models",
        "does not run RAG",
        "does not generate explanation content",
        "cannot prove that historical interpretation is complete",
    ]
    for term in boundary_terms:
        assert term in runbook

    assert "docs/real_data_import_runbook.md" in readme
    assert "docs/real_data_import_runbook.md" in readiness
    assert "docs/real_data_import_runbook.md" in handoff
    assert "Real data import runbook reviewed" in staging_record


def test_real_data_preimport_final_checklist_covers_import_gate() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "real_data_import_runbook.md").read_text(encoding="utf-8")
    seed_review = (PROJECT_ROOT / "docs" / "real_exhibit_seed_review.md").read_text(
        encoding="utf-8"
    )
    operator_runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(
        encoding="utf-8"
    )
    checklist = (PROJECT_ROOT / "docs" / "real_data_preimport_final_checklist.md").read_text(
        encoding="utf-8"
    )

    required_terms = [
        "Required Inputs",
        "Gate 1: Source Package And Manual Review",
        "Gate 2: Seed Structure",
        "Gate 3: Runtime And Migration",
        "Gate 4: Backup And Restore",
        "Gate 5: Seed Dry-Run",
        "Gate 6: Pre-Import Runtime Evidence",
        "Gate 7: Import Authorization",
        "Gate 8: Immediate Post-Import Checks",
        "Gate 9: GeniOS Source-Safety Smoke",
        "docs/real_exhibit_seed_review.md",
        "docs/exhibit_seed_format.md",
        "docs/staging_validation_record.md",
        "docs/backup_rollback_drill.md",
        "docs/operator_evidence_package_checklist.md",
        "docs/production_readiness_decision_checklist.md",
        "docs/operator_post_run_review.md",
        "source_reference",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\validate_runtime_config.py --profile production",
        "python scripts\\rehearse_migrations.py",
        "alembic upgrade head",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "--require-non-empty",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run <verified-seed-file>",
        "python scripts\\deployment_self_check.py --base-url",
        "python scripts\\validate_backend_readiness.py --base-url",
        "python scripts\\import_exhibits.py <verified-seed-file>",
        "GET /api/exhibits/source-report",
        "GET /api/exhibits/quality-report",
        "GET /api/audit-logs?action=exhibits_imported",
        "GET /api/audit-logs/stats",
        "GET /api/system/operational-alerts",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "grounding_sources_complete=true",
        "source_safety.ready_for_generation=true",
        "missing_exhibit_ids=[]",
        "unsourced_exhibit_ids=[]",
        "X-HistoryGuide-Request-Id",
        "rollback_candidate",
    ]
    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not create, infer, rewrite, or generate historical facts",
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
    ]
    for term in boundary_terms:
        assert term in checklist

    for document in (readme, readiness, handoff, runbook, seed_review, operator_runbook):
        assert "docs/real_data_preimport_final_checklist.md" in document


def test_backup_rollback_drill_covers_recovery_gates() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(encoding="utf-8")
    drill = (PROJECT_ROOT / "docs" / "backup_rollback_drill.md").read_text(encoding="utf-8")

    required_terms = [
        "Pre-Change Runtime Gate",
        "Backup Gate",
        "Change Gate",
        "Post-Change Validation Gate",
        "Rollback Decision",
        "Rollback Execution Record",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "--require-non-empty",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\deployment_self_check.py",
        "GET /api/genios/handoff/{session_id}",
        "source_safety.ready_for_generation",
        "grounding_sources_complete",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "X-HistoryGuide-Request-Id",
    ]

    for term in required_terms:
        assert term in drill

    boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not train models",
        "does not run RAG",
        "does not generate explanation content",
        "does not define a GeniOS prompt",
        "digital humans",
        "AR/VR",
    ]
    for term in boundary_terms:
        assert term in drill

    for document in (readme, readiness, production, handoff):
        assert "docs/backup_rollback_drill.md" in document

    assert "Backup and rollback drill reviewed" in staging_record
    assert "Rollback required" in staging_record


def test_operator_runbook_covers_backend_operations() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    example = (
        PROJECT_ROOT / "docs" / "examples" / "deployment_environment_validation.example.md"
    ).read_text(encoding="utf-8")

    required_terms = [
        "local fixture demo",
        "verified exhibit data dry-run",
        "verified exhibit data import",
        "staging migration validation",
        "Web/H5 integration check",
        "GeniOS handoff evidence run",
        "backup and rollback drill",
        "incident triage",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\deployment_self_check.py",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run",
        "python scripts\\rehearse_migrations.py",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/genios/handoff/{session_id}",
        "grounding_sources_complete=true",
        "source_safety.ready_for_generation=true",
        "X-HistoryGuide-Request-Id",
    ]
    for term in required_terms:
        assert term in runbook

    boundary_terms = [
        "does not train models",
        "does not replace GeniOS",
        "does not run RAG",
        "does not generate explanation content",
        "does not define GeniOS prompts",
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "implement digital humans",
        "implement AR/VR",
    ]
    for term in boundary_terms:
        assert term in runbook

    for document in (readme, readiness, production, handoff):
        assert "docs/operator_runbook.md" in document

    for document in (readme, readiness, production, runbook):
        assert "docs/examples/deployment_environment_validation.example.md" in document

    example_terms = [
        "placeholder values only",
        "not evidence that any real staging, production-like, or museum deployment has been validated",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\deployment_self_check.py",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "HISTORYGUIDE_CORS_ORIGINS",
        "X-HistoryGuide-Request-Id",
        "GET /api/genios/handoff/{session_id}",
        "grounding_sources_complete",
        "source_safety.ready_for_generation",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "Rollback required",
    ]
    for term in example_terms:
        assert term in example

    example_boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not train models",
        "does not run RAG",
        "does not generate explanation content",
        "does not define GeniOS prompts",
        "digital human or AR/VR",
    ]
    for term in example_boundary_terms:
        assert term in example


def test_incident_response_checklist_covers_backend_triage() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "docs" / "incident_response_checklist.md").read_text(
        encoding="utf-8"
    )

    required_terms = [
        "First Five Minutes",
        "GET /ready",
        "GET /api/system/database",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "GET /api/exhibits/source-report",
        "GET /api/exhibits/quality-report",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/visitor-states/{session_id}/visit-events",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "X-HistoryGuide-Request-Id",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "source_safety.ready_for_generation",
        "grounding_sources_complete",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "docs/backup_rollback_drill.md",
        "docs/operator_runbook.md",
    ]
    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not prove historical accuracy",
    ]
    for term in boundary_terms:
        assert term in checklist

    for document in (readme, readiness, production, handoff, runbook):
        assert "docs/incident_response_checklist.md" in document


def test_monitoring_alert_examples_cover_production_like_signals() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    logging_doc = (PROJECT_ROOT / "docs" / "centralized_logging.md").read_text(encoding="utf-8")
    incident = (PROJECT_ROOT / "docs" / "incident_response_checklist.md").read_text(
        encoding="utf-8"
    )
    monitoring = (PROJECT_ROOT / "docs" / "monitoring_alert_examples.md").read_text(
        encoding="utf-8"
    )
    example = (
        PROJECT_ROOT / "docs" / "examples" / "operational_alerts_attention_required.example.json"
    ).read_text(encoding="utf-8")

    required_terms = [
        "GET /ready",
        "GET /api/system/database",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/visitor-states/{session_id}/visit-events",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "X-HistoryGuide-Request-Id",
        "source_safety.ready_for_generation",
        "grounding_sources_complete",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "no_exhibit_records",
        "unsourced_exhibits",
        "exhibit_metadata_gaps",
        "visitor_state_integrity_issues",
        "audit_logs_empty",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "rollback_candidate",
        "docs/incident_response_checklist.md",
        "docs/backup_rollback_drill.md",
    ]
    for term in required_terms:
        assert term in monitoring

    boundary_terms = [
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not prove historical accuracy",
        "not visitor identity",
        "not GeniOS prompt input",
    ]
    for term in boundary_terms:
        assert term in monitoring

    for document in (readme, readiness, production, handoff, runbook, logging_doc, incident):
        assert "docs/monitoring_alert_examples.md" in document

    for document in (readme, readiness, production, runbook, monitoring):
        assert "docs/examples/operational_alerts_attention_required.example.json" in document

    example_terms = [
        '"status": "attention_required"',
        '"fail_count": 2',
        '"warn_count": 3',
        '"no_exhibit_records"',
        '"unsourced_exhibits"',
        '"exhibit_metadata_gaps"',
        '"visitor_state_integrity_issues"',
        '"audit_logs_empty"',
        "Placeholder monitoring example only",
        "not evidence that any real staging, production-like, or museum deployment has produced these alerts",
    ]
    for term in example_terms:
        assert term in example


def test_operator_evidence_package_checklist_covers_handoff_evidence() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    incident = (PROJECT_ROOT / "docs" / "incident_response_checklist.md").read_text(
        encoding="utf-8"
    )
    monitoring = (PROJECT_ROOT / "docs" / "monitoring_alert_examples.md").read_text(
        encoding="utf-8"
    )
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(
        encoding="utf-8"
    )
    checklist = (PROJECT_ROOT / "docs" / "operator_evidence_package_checklist.md").read_text(
        encoding="utf-8"
    )
    example = (
        PROJECT_ROOT / "docs" / "examples" / "operator_evidence_package.example.md"
    ).read_text(encoding="utf-8")

    required_terms = [
        "Package Metadata",
        "Required Evidence Files",
        "Runtime Evidence",
        "Data And Migration Evidence",
        "Visit Flow Evidence",
        "GeniOS Handoff Evidence",
        "Monitoring And Incident Evidence",
        "Audit Evidence",
        "Redaction Checklist",
        "Final Package Decision",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\deployment_self_check.py --base-url",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run",
        "python scripts\\rehearse_migrations.py",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/visitor-states/{session_id}/visit-events",
        "GET /api/recommendations/{session_id}",
        "GET /api/visit-routes/{session_id}/plan",
        "GET /api/visits/{session_id}/summary",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "GET /api/audit-logs/stats",
        "GET /api/audit-logs",
        "GET /api/system/operational-alerts",
        "X-HistoryGuide-Request-Id",
        "source_safety.ready_for_generation",
        "grounding_sources_complete",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "rollback_candidate",
        "proceed_with_warnings",
        "rollback_required",
    ]
    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "not visitor identity",
        "not GeniOS prompt input",
    ]
    for term in boundary_terms:
        assert term in checklist

    redaction_terms = [
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "X-HistoryGuide-Api-Key",
        "X-HistoryGuide-Operator-Key",
        "full database URLs",
        "private GeniOS prompts",
    ]
    for term in redaction_terms:
        assert term in checklist

    for document in (readme, readiness, production, handoff, runbook, incident, monitoring):
        assert "docs/operator_evidence_package_checklist.md" in document

    for document in (readme, readiness, production, handoff, runbook, checklist):
        assert "docs/examples/operator_evidence_package.example.md" in document

    assert "Operator evidence package path" in staging_record
    assert "Evidence package completed" in staging_record

    example_terms = [
        "placeholder values only",
        "not evidence that any real staging, production-like, or museum deployment has been validated",
        "Package Metadata",
        "Runtime Evidence",
        "Data And Migration Evidence",
        "Visit Flow Evidence",
        "GeniOS Handoff Evidence",
        "Monitoring And Incident Evidence",
        "Audit Evidence",
        "Redaction Checklist",
        "Final Package Decision",
        "docs/examples/backend_readiness_validation.example.md",
        "docs/examples/deployment_environment_validation.example.md",
        "docs/examples/genios_handoff_evidence.example.md",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\deployment_self_check.py --base-url https://staging-historyguide.example.test",
        "python scripts\\validate_backend_readiness.py --base-url https://staging-historyguide.example.test",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/genios/handoff/{session_id}",
        "GET /api/audit-logs/stats",
        "X-HistoryGuide-Request-Id",
        "source_safety.ready_for_generation=true",
        "grounding_sources_complete=true",
        "missing_exhibit_ids=[]",
        "unsourced_exhibit_ids=[]",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "rollback_candidate",
        "proceed_with_warnings",
    ]
    for term in example_terms:
        assert term in example

    example_boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "not visitor identity",
        "not GeniOS prompt input",
    ]
    for term in example_boundary_terms:
        assert term in example


def test_production_readiness_decision_checklist_covers_go_no_go_gates() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    evidence = (PROJECT_ROOT / "docs" / "operator_evidence_package_checklist.md").read_text(
        encoding="utf-8"
    )
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(
        encoding="utf-8"
    )
    checklist = (
        PROJECT_ROOT / "docs" / "production_readiness_decision_checklist.md"
    ).read_text(encoding="utf-8")
    example = (
        PROJECT_ROOT / "docs" / "examples" / "production_readiness_decision.example.md"
    ).read_text(encoding="utf-8")

    required_terms = [
        "Decision Metadata",
        "Required Evidence",
        "Gate 1: Runtime Configuration",
        "Gate 2: Read-Only Runtime Self-Check",
        "Gate 3: Database And Migration",
        "Gate 4: Data Safety And Backup",
        "Gate 5: Visit Flow",
        "Gate 6: GeniOS Handoff And Source Safety",
        "Gate 7: Monitoring And Incident Preparedness",
        "Gate 8: Evidence Package",
        "Final Decision Rules",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\validate_runtime_config.py --profile production",
        "python scripts\\deployment_self_check.py --base-url",
        "python scripts\\validate_backend_readiness.py --base-url",
        "--session-id <session-id>",
        "--require-visit-events",
        "python scripts\\rehearse_migrations.py",
        "alembic upgrade head",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run",
        "GET /health",
        "GET /ready",
        "GET /api/system/database",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/visitor-states/{session_id}/visit-events",
        "GET /api/recommendations/{session_id}",
        "GET /api/visit-routes/{session_id}/plan",
        "GET /api/visits/{session_id}/summary",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "X-HistoryGuide-Request-Id",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "source_safety.ready_for_generation=true",
        "grounding_sources_complete=true",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "unsourced_exhibits",
        "visitor_state_integrity_issues",
        "audit_logs_empty",
        "rollback_candidate",
        "proceed_with_warnings",
        "rollback_required",
        "Passing tests alone are not production readiness evidence",
        "docs/operator_evidence_package_checklist.md",
        "docs/staging_validation_record.md",
        "docs/backup_rollback_drill.md",
        "docs/genios_handoff_evidence_template.md",
        "docs/web_h5_integration_checklist.md",
        "docs/monitoring_alert_examples.md",
        "docs/incident_response_checklist.md",
    ]
    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
    ]
    for term in boundary_terms:
        assert term in checklist

    for document in (readme, readiness, production, handoff, runbook, evidence):
        assert "docs/production_readiness_decision_checklist.md" in document

    for document in (readme, readiness, production, handoff, runbook, checklist):
        assert "docs/examples/production_readiness_decision.example.md" in document

    assert "Production readiness decision checklist completed" in staging_record
    assert "Production readiness decision" in staging_record

    example_terms = [
        "placeholder values only",
        "not evidence that any real staging, production-like, museum-site, or production deployment has been validated",
        "Decision Metadata",
        "Required Evidence Attached",
        "Gate 1: Runtime Configuration",
        "Gate 2: Read-Only Runtime Self-Check",
        "Gate 3: Database And Migration",
        "Gate 4: Data Safety And Backup",
        "Gate 5: Visit Flow",
        "Gate 6: GeniOS Handoff And Source Safety",
        "Gate 7: Monitoring And Incident Preparedness",
        "Gate 8: Evidence Package",
        "Final Decision",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\validate_runtime_config.py --profile production",
        "python scripts\\deployment_self_check.py --base-url https://staging-historyguide.example.test",
        "python scripts\\validate_backend_readiness.py --base-url https://staging-historyguide.example.test",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/genios/handoff/{session_id}",
        "X-HistoryGuide-Request-Id",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "source_safety.ready_for_generation=true",
        "grounding_sources_complete=true",
        "missing_exhibit_ids=[]",
        "unsourced_exhibit_ids=[]",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "unsourced_exhibits",
        "visitor_state_integrity_issues",
        "audit_logs_empty",
        "rollback_candidate",
        "proceed_with_warnings",
        "blocked",
        "rollback_required",
        "Passing tests alone are not production readiness evidence",
        "docs/examples/operator_evidence_package.example.md",
    ]
    for term in example_terms:
        assert term in example

    example_boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not certify Web/H5 or GeniOS production readiness outside the backend integration contract",
    ]
    for term in example_boundary_terms:
        assert term in example


def test_operator_final_prerun_checklist_covers_last_mile_gates() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    decision = (
        PROJECT_ROOT / "docs" / "production_readiness_decision_checklist.md"
    ).read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "docs" / "operator_final_prerun_checklist.md").read_text(
        encoding="utf-8"
    )

    required_terms = [
        "Required Inputs",
        "Gate 1: Environment And Access",
        "Gate 2: Read-Only Backend State",
        "Gate 3: Data, Migration, And Rollback",
        "Gate 4: Real Visit Session",
        "Gate 5: GeniOS Handoff Source Safety",
        "Gate 6: Monitoring And Incident Readiness",
        "Gate 7: Final Decision",
        "Final Operator Statement",
        "docs/staging_validation_record.md",
        "docs/operator_evidence_package_checklist.md",
        "docs/production_readiness_decision_checklist.md",
        "docs/genios_handoff_evidence_template.md",
        "docs/web_h5_integration_checklist.md",
        "docs/backup_rollback_drill.md",
        "docs/monitoring_alert_examples.md",
        "docs/incident_response_checklist.md",
        "docs/examples/staging_validation_record.example.md",
        "docs/examples/backend_readiness_validation.example.md",
        "docs/examples/operator_evidence_package.example.md",
        "docs/examples/production_readiness_decision.example.md",
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\validate_runtime_config.py --profile production",
        "python scripts\\deployment_self_check.py --base-url",
        "python scripts\\validate_backend_readiness.py --base-url",
        "--session-id <session-id>",
        "--require-visit-events",
        "python scripts\\rehearse_migrations.py",
        "alembic upgrade head",
        "python scripts\\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\import_exhibits.py --dry-run",
        "GET /health",
        "GET /ready",
        "GET /api/system/database",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/visitor-states/{session_id}/visit-events",
        "GET /api/recommendations/{session_id}",
        "GET /api/visit-routes/{session_id}/plan",
        "GET /api/visits/{session_id}/summary",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_LOG_FORMAT=json",
        "X-HistoryGuide-Request-Id",
        "grounding_sources_complete=true",
        "source_safety.ready_for_generation=true",
        "missing_exhibit_ids=[]",
        "unsourced_exhibit_ids=[]",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "unsourced_exhibits",
        "visitor_state_integrity_issues",
        "audit_logs_empty",
        "rollback_candidate",
        "incident owner",
        "rollback owner",
        "proceed_with_warnings",
        "blocked",
        "rollback_required",
        "Passing tests alone are not production readiness evidence",
    ]
    for term in required_terms:
        assert term in checklist

    boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not certify Web/H5 or GeniOS production readiness outside the backend integration contract",
    ]
    for term in boundary_terms:
        assert term in checklist

    for document in (readme, readiness, production, runbook, handoff, decision):
        assert "docs/operator_final_prerun_checklist.md" in document


def test_operator_post_run_review_covers_closeout_evidence() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    prerun = (PROJECT_ROOT / "docs" / "operator_final_prerun_checklist.md").read_text(
        encoding="utf-8"
    )
    review = (PROJECT_ROOT / "docs" / "operator_post_run_review.md").read_text(
        encoding="utf-8"
    )

    required_terms = [
        "Run Metadata",
        "Evidence Chain",
        "Runtime Outcome",
        "Request Id Evidence",
        "Visit Flow Review",
        "GeniOS Handoff Review",
        "Data And Audit Review",
        "Monitoring And Incident Review",
        "Evidence Package Update",
        "Follow-Up Decisions",
        "docs/operator_final_prerun_checklist.md",
        "docs/staging_validation_record.md",
        "docs/operator_evidence_package_checklist.md",
        "docs/production_readiness_decision_checklist.md",
        "docs/genios_handoff_evidence_template.md",
        "docs/web_h5_integration_checklist.md",
        "docs/backup_rollback_drill.md",
        "docs/incident_response_checklist.md",
        "docs/monitoring_alert_examples.md",
        "docs/examples/backend_readiness_validation.example.md",
        "docs/examples/operator_evidence_package.example.md",
        "docs/examples/production_readiness_decision.example.md",
        "completed_with_warnings",
        "blocked_before_start",
        "aborted_during_run",
        "rollback_required",
        "GET /health",
        "GET /ready",
        "GET /api/system/operational-alerts",
        "status_code = 401",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "rollback_candidate",
        "X-HistoryGuide-Request-Id",
        "POST /api/visitor-states",
        "POST /api/visitor-states/{session_id}/visit-events",
        "GET /api/visitor-states/{session_id}/integrity",
        "GET /api/recommendations/{session_id}",
        "GET /api/visit-routes/{session_id}/plan",
        "GET /api/visits/{session_id}/summary",
        "GET /api/genios/context/{session_id}",
        "GET /api/genios/grounding/{session_id}",
        "GET /api/genios/preflight/{session_id}",
        "GET /api/genios/handoff/{session_id}",
        "grounding_sources_complete",
        "source_safety.ready_for_generation",
        "missing_exhibit_ids",
        "unsourced_exhibit_ids",
        "GET /api/audit-logs/stats",
        "visitor_state_created",
        "visitor_state_updated",
        "visit_event_recorded",
        "exhibits_imported",
        "closed_clean",
        "closed_with_warnings",
        "follow_up_required",
        "incident_follow_up_required",
        "rollback_follow_up_required",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "X-HistoryGuide-Api-Key",
        "X-HistoryGuide-Operator-Key",
    ]
    for term in required_terms:
        assert term in review

    boundary_terms = [
        "does not prove historical accuracy",
        "does not replace museum or expert review",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not certify Web/H5 or GeniOS production readiness outside the backend integration contract",
    ]
    for term in boundary_terms:
        assert term in review

    for document in (readme, readiness, production, runbook, handoff, prerun):
        assert "docs/operator_post_run_review.md" in document


def test_operational_docs_cover_read_only_backend_readiness_validator() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    runbook = (PROJECT_ROOT / "docs" / "operator_runbook.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    evidence = (PROJECT_ROOT / "docs" / "operator_evidence_package_checklist.md").read_text(
        encoding="utf-8"
    )
    decision = (
        PROJECT_ROOT / "docs" / "production_readiness_decision_checklist.md"
    ).read_text(encoding="utf-8")
    script = (PROJECT_ROOT / "scripts" / "validate_backend_readiness.py").read_text(
        encoding="utf-8"
    )
    example = (
        PROJECT_ROOT / "docs" / "examples" / "backend_readiness_validation.example.md"
    ).read_text(encoding="utf-8")

    command_terms = [
        "python scripts\\validate_backend_readiness.py --base-url",
        "--api-key <business-key>",
        "--operator-key <operator-key>",
        "--require-exhibits",
        "--require-sourced-exhibits",
        "--require-audit-logs",
        "--require-clean-operational-alerts",
        "--session-id <session-id>",
        "--require-visit-events",
    ]
    for document in (readme, readiness, production, handoff, evidence, decision):
        for term in command_terms:
            assert term in document

    coverage_terms = [
        "readiness",
        "database status",
        "operational alerts",
        "exhibit source",
        "quality reports",
        "audit log stats",
        "Visitor State integrity",
        "visit events",
        "recommendations",
        "route plan",
        "visit summary",
        "GeniOS grounding",
        "GeniOS preflight",
        "GeniOS handoff",
        "source-safety",
        "X-HistoryGuide-Request-Id",
    ]
    for document in (readme, production, handoff):
        for term in coverage_terms:
            assert term in document

    boundary_terms = [
        "does not write to the database",
        "does not print key values",
        "does not validate historical accuracy",
        "does not run RAG",
        "does not generate explanation content",
    ]
    for document in (readme, readiness, production, handoff, script):
        for term in boundary_terms:
            assert term in document

    for document in (readme, readiness, production, runbook, handoff, evidence, decision):
        assert "docs/examples/backend_readiness_validation.example.md" in document

    example_terms = [
        "placeholder values only",
        "not evidence that any real staging, production-like, or museum deployment has been validated",
        "python scripts\\validate_backend_readiness.py --base-url https://staging-historyguide.example.test",
        "--session-id staging-session-001",
        "[PASS] readiness",
        "[PASS] database_status",
        "[PASS] operational_alerts",
        "[PASS] exhibit_source_report",
        "[PASS] audit_log_stats",
        "[PASS] visitor_state_integrity",
        "[PASS] genios_grounding",
        "[PASS] genios_preflight",
        "[PASS] genios_handoff",
        "request_id=example-readiness-001",
        "source_safety.ready_for_generation=True",
        "grounding_sources_complete=True",
        "missing_exhibit_ids=[]",
        "unsourced_exhibit_ids=[]",
        "blocking_check_names=[]",
    ]
    for term in example_terms:
        assert term in example

    example_boundary_terms = [
        "does not write to the database",
        "does not print key values",
        "does not validate historical accuracy",
        "does not run RAG",
        "does not generate explanation content",
        "does not train models",
        "does not define GeniOS prompts",
        "does not implement digital humans",
        "does not implement AR/VR",
        "does not replace museum or expert review",
    ]
    for term in example_boundary_terms:
        assert term in example


def test_production_hardening_document_covers_deployment_gates() -> None:
    document = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")

    required_terms = [
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "HISTORYGUIDE_CORS_ORIGINS",
        "HISTORYGUIDE_DATABASE_URL",
        "GET /api/system/database",
        "scripts\\deployment_self_check.py",
        "python scripts\\validate_runtime_config.py",
        "python scripts\\export_exhibits.py",
        "python scripts\\verify_exhibit_backup.py",
        "python scripts\\rehearse_exhibit_restore.py",
        "python scripts\\rehearse_migrations.py",
        "SQLite Boundary",
        "PostgreSQL Migration Gate",
        "Do not switch to PostgreSQL only by changing `HISTORYGUIDE_DATABASE_URL`",
        "source_safety.ready_for_generation=true",
        "X-HistoryGuide-Operator-Key",
        "Rollback Checklist",
        "Runtime Monitoring Checklist",
        "does not train models",
        "does not write to the database",
        "does not print key values",
    ]

    for term in required_terms:
        assert term in document


def test_operational_docs_cover_runtime_config_validation() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    deployment = (PROJECT_ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "python scripts\\validate_runtime_config.py --profile staging",
        "python scripts\\validate_runtime_config.py --profile production",
        "API key presence",
        "operator key separation",
        "CORS wildcard risk",
        "database URL profile risk",
        "log level",
        "log format",
        "without printing secret values",
    ]

    for document in (readme, deployment, production, readiness, handoff):
        for term in required_terms:
            assert term in document

    boundary_terms = [
        "does not connect to the database",
        "does not validate historical content",
        "GeniOS",
        "RAG",
        "generate explanation content",
    ]
    for term in boundary_terms:
        assert term in production
        assert term in handoff


def test_api_contract_contains_complete_genios_handoff_example() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")

    required_terms = [
        "Example ready handoff response using non-historical fixture data",
        '"source_safety"',
        '"ready_for_generation": true',
        '"grounding_source_references"',
        '"visitor_state_integrity"',
        '"grounding_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"]',
        '"route_plan"',
        '"visit_summary"',
        '"handoff_note"',
        "The backend does not generate explanation text.",
    ]

    for term in required_terms:
        assert term in document


def test_database_migration_scaffold_is_documented() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    document = (PROJECT_ROOT / "docs" / "database_migrations.md").read_text(encoding="utf-8")

    required_terms = [
        "Alembic migration scaffold",
        "alembic.ini",
        "migrations/env.py",
        "migrations/versions/0001_initial_schema.py",
        "migrations/versions/0002_audit_logs.py",
        "scripts\\rehearse_migrations.py",
        "scripts\\validate_staging_database.py",
        "isolated temporary SQLite database",
        "audit_logs",
        "alembic upgrade head",
        "alembic revision --autogenerate",
        "source_safety.ready_for_generation=true",
        "Do not switch to PostgreSQL only by changing `HISTORYGUIDE_DATABASE_URL`",
        "does not train models",
    ]

    assert "docs/database_migrations.md" in readme
    for term in required_terms:
        assert term in document


def test_operational_docs_cover_read_only_staging_database_validation() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    migrations = (PROJECT_ROOT / "docs" / "database_migrations.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    staging_record = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(encoding="utf-8")

    command_terms = [
        "python scripts\\validate_staging_database.py",
        "--require-exhibits",
        "--require-sourced-exhibits",
        "--require-audit-logs",
    ]
    for document in (readme, migrations, production, readiness, handoff, staging_record):
        for term in command_terms:
            assert term in document

    coverage_terms = [
        "current Alembic head",
        "empty `source_reference`",
        "Visitor State count",
        "visit-event count",
        "audit-log count",
        "read-only",
    ]
    for document in (migrations, production, readiness, handoff):
        for term in coverage_terms:
            assert term in document

    boundary_terms = [
        "does not run migrations",
        "import records",
        "write audit logs",
        "validate historical accuracy",
        "run RAG",
        "generate explanation content",
    ]
    for document in (migrations, production, handoff):
        for term in boundary_terms:
            assert term in document


def test_operational_docs_cover_migration_rehearsal() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    deployment = (PROJECT_ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    migrations = (PROJECT_ROOT / "docs" / "database_migrations.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "python scripts\\rehearse_migrations.py",
        "alembic upgrade head",
        "isolated temporary SQLite database",
        "current Alembic revision",
        "core tables",
        "does not modify the configured application database",
        "does not import",
        "PostgreSQL production-ready",
    ]

    for document in (readme, deployment, migrations, production, handoff):
        for term in required_terms:
            assert term in document


def test_operational_docs_cover_staging_validation_record() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")
    template = (PROJECT_ROOT / "docs" / "staging_validation_record.md").read_text(encoding="utf-8")
    example = (
        PROJECT_ROOT / "docs" / "examples" / "staging_validation_record.example.md"
    ).read_text(encoding="utf-8")

    required_template_terms = [
        "Runtime Config Gate",
        "Migration Gate",
        "Data Safety Gate",
        "Runtime Endpoint Gate",
        "Historical Content Safety Gate",
        "GeniOS Handoff Gate",
        "Centralized Logging Gate",
        "source_safety.ready_for_generation",
        "does not prove historical accuracy",
        "does not train models",
        "does not run RAG",
        "does not generate explanation content",
    ]

    for term in required_template_terms:
        assert term in template

    for term in ("docs/staging_validation_record.md", "staging evidence", "runtime config"):
        assert term in production
        assert term in readiness

    assert "docs/staging_validation_record.md" in readme
    assert "docs/staging_validation_record.md" in handoff
    assert "This example uses placeholder values only" in example
    assert "not evidence that staging has been validated" in example


def test_alembic_scaffold_tracks_current_models() -> None:
    alembic_ini = (PROJECT_ROOT / "alembic.ini").read_text(encoding="utf-8")
    env_py = (PROJECT_ROOT / "migrations" / "env.py").read_text(encoding="utf-8")
    initial_migration = (
        PROJECT_ROOT / "migrations" / "versions" / "0001_initial_schema.py"
    ).read_text(encoding="utf-8")
    audit_migration = (
        PROJECT_ROOT / "migrations" / "versions" / "0002_audit_logs.py"
    ).read_text(encoding="utf-8")

    assert "script_location = migrations" in alembic_ini
    assert "settings.database_url" in env_py
    assert "Base.metadata" in env_py
    assert "compare_type=True" in env_py

    required_schema_terms = [
        '"exhibits"',
        '"visitor_states"',
        '"visitor_visit_events"',
        '"source_reference"',
        '"visited_history"',
        '"event_time"',
    ]
    for term in required_schema_terms:
        assert term in initial_migration

    required_audit_terms = [
        '"audit_logs"',
        '"action"',
        '"resource_type"',
        '"resource_id"',
        '"actor"',
        '"details"',
        '"created_at"',
    ]
    for term in required_audit_terms:
        assert term in audit_migration


def test_api_contract_documents_audit_log_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")

    required_terms = [
        "GET /api/audit-logs",
        "GET /api/audit-logs/stats",
        "total_logs",
        "visitor_state_created",
        "visitor_state_updated",
        "visit_event_recorded",
        "exhibits_imported",
        "operator traceability",
        "do not infer visitor profiles",
        "generate explanation content",
    ]

    for term in required_terms:
        assert term in document


def test_api_contract_documents_operational_alert_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")

    required_terms = [
        "GET /api/system/operational-alerts",
        "unsourced_exhibits",
        "Visitor State timeline drift",
        "missing audit evidence",
        "does not inspect historical accuracy",
        "infer visitor profiles",
        "generate explanation content",
    ]

    for term in required_terms:
        assert term in document


def test_api_contract_documents_operator_api_key_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")

    required_terms = [
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "X-HistoryGuide-Operator-Key",
        "GET /api/audit-logs",
        "GET /api/audit-logs/stats",
        "GET /api/system/operational-alerts",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "ordinary business APIs require `X-HistoryGuide-Api-Key`",
        "Valid HistoryGuide operator API key is required.",
    ]

    for term in required_terms:
        assert term in document


def test_api_contract_documents_request_id_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "X-HistoryGuide-Request-Id",
        "correlate",
        "not authentication",
        "visitor identity",
        "historical evidence",
    ]

    for document_text in (document, readme, production, handoff):
        for term in required_terms:
            assert term in document_text


def test_operational_docs_cover_structured_request_logging() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    deployment = (PROJECT_ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    logging_doc = (PROJECT_ROOT / "docs" / "centralized_logging.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "HISTORYGUIDE_LOG_FORMAT",
        "json",
        "request_id",
        "http_method",
        "path",
        "status_code",
        "elapsed_ms",
        "centralized",
    ]

    for document_text in (readme, deployment, logging_doc, production, readiness, handoff):
        for term in required_terms:
            assert term in document_text

    logging_terms = [
        "docs/examples/structured_request_log.json",
        "X-HistoryGuide-Request-Id",
        "deployment_self_check.py",
        "status_code >= 500",
        "elapsed_ms > 1000",
        "Never log",
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_OPERATOR_API_KEY",
        "not authentication",
        "not historical evidence",
        "not GeniOS prompt input",
    ]
    for term in logging_terms:
        assert term in logging_doc


def test_api_contract_documents_security_status_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")

    required_terms = [
        "GET /api/system/security-status",
        "business_api_key_configured",
        "operator_api_key_configured",
        "public_probe_paths",
        "operator_paths",
        "never returns configured key values",
        "not a replacement for full RBAC",
        "does not generate explanation content",
    ]

    for term in required_terms:
        assert term in document


def test_api_contract_documents_access_policy_boundary() -> None:
    document = (PROJECT_ROOT / "docs" / "api_contract.md").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    deployment = (PROJECT_ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "GET /api/system/access-policy",
        "public_probe",
        "business_api",
        "operator_api",
        "local_operator_workflow",
        "X-HistoryGuide-Operator-Key",
        "never returns configured key values",
        "full RBAC",
        "does not generate explanation content",
    ]

    for term in required_terms:
        assert term in document

    shared_terms = [
        "GET /api/system/access-policy",
        "coarse",
        "without exposing key values",
        "full RBAC",
    ]
    for document_text in (readme, deployment, production, readiness, handoff):
        for term in shared_terms:
            assert term in document_text


def test_deployment_docs_cover_read_only_self_check() -> None:
    deployment = (PROJECT_ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "python scripts\\deployment_self_check.py --base-url",
        "GET /api/system/access-policy",
        "GET /api/system/security-status",
        "GET /api/system/operational-alerts",
        "X-HistoryGuide-Request-Id",
        "log correlation",
        "does not write to the database",
        "does not print key values",
    ]

    for term in required_terms:
        assert term in deployment
        assert term in handoff


def test_operational_docs_cover_exhibit_backup_verification() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "python scripts\\verify_exhibit_backup.py",
        "--require-non-empty",
        "source_reference",
        "does not prove historical accuracy",
        "does not import records",
    ]

    for document in (readme, production, readiness, handoff):
        for term in required_terms:
            assert term in document


def test_operational_docs_cover_restore_rehearsal() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    production = (PROJECT_ROOT / "docs" / "production_hardening.md").read_text(encoding="utf-8")
    readiness = (PROJECT_ROOT / "docs" / "operational_readiness.md").read_text(encoding="utf-8")
    handoff = (PROJECT_ROOT / "docs" / "mvp_handoff.md").read_text(encoding="utf-8")

    required_terms = [
        "python scripts\\rehearse_exhibit_restore.py",
        "isolated in-memory SQLite database",
        "does not modify the configured application database",
        "does not prove historical accuracy",
    ]

    for document in (readme, production, readiness, handoff):
        for term in required_terms:
            assert term in document
