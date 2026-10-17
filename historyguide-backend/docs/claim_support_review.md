# Claim-to-Quote Human Review

Shared deployments must set `HISTORYGUIDE_CLAIM_SUPPORT_REQUIRED=true`, migrate to Alembic head, and keep the operator key separate from the business key. This gate is **not** an automated semantic evaluator. A curator must check the meaning of each exact claim against its full source context, including negation, dates, scope and ambiguity. The `reviewer` text is an operator-supplied audit label, not cryptographic identity; the operator key must be held only by trusted staff.

1. Approve a real source through `/api/evidence/sources/{source_id}/approve` after checking provenance. Development fixtures cannot be approved.
2. Submit `POST /api/evidence/claim-support` with `source_id`, an exact `evidence_quote` present in that source, and a `claim_text` present in the quote. This creates a **draft** candidate, not permission to release.
3. A curator checks the full source and calls `POST /api/evidence/claim-support/{id}/approve` with `{"reviewer":"<staff identifier>","support_confirmed":true}` using `X-HistoryGuide-Operator-Key`. `false` is rejected.
4. Use `POST /api/genios/answers/history` or `/exhibit` with every answer claim cited. In strict mode each exact citation pair needs an approved, current-version review. A successful response sets `claim_support_reviewed=true`, but `semantic_verified=false`: the system has an auditable human decision, not proof that a language model understood the source.
5. To withdraw support, call `POST /api/evidence/claim-support/{id}/revoke` with a reviewer label. New release attempts then fail. A source metadata/body change also invalidates its approval; reapprove the source and create/review new claim candidates.

Strict mode disables the legacy multi-call prepare/review/finalize HTTP routes because their persisted review receipt cannot re-check citation decisions at finalization. It also rejects legacy `POST /api/genios/review`, whose `safe_answer` previously echoed a structurally accepted draft without per-claim approval. Existing Coze Handoff/Review tools are **not** equivalent to this release path. Deploy the new backend to isolated staging, import the new one-call tool there, make it the mandatory final-output gate, and verify authentic Coze traces before replacing the old configuration.

In strict mode, the final claim check locks the current source and approval rows with `SELECT FOR UPDATE` until the same transaction commits answer finalization. Finalization audit records the approval IDs used, without storing quote or answer text. PostgreSQL serializes a concurrent source/claim revocation on these rows; the release is considered valid at its commit point, and a later revocation blocks later releases. SQLite ignores row-level `FOR UPDATE`, so local SQLite tests do **not** prove this concurrency property.

Run the multi-connection probe only against an isolated, migrated PostgreSQL staging database. It writes one uniquely named synthetic source and approval, invokes the real strict release check in one transaction, attempts revocation from a second connection, and cleans its source, approval and related audit records by default. It refuses SQLite and refuses to write without the explicit acknowledgement flag. Do not point it at production.

```powershell
python scripts\verify_postgres_claim_release_lock.py --acknowledge-staging-write-test
```

The process must exit `0` and report that revocation stayed blocked until the release transaction committed, that the next transaction observed revocation, and that probe records were cleaned. `--keep-probe-records` is only for failed-staging investigation. A passing probe verifies database lock behavior for this transaction boundary; it does not prove curator identity, historical truth, Coze routing, or all production concurrency behavior.

The operator must never paste keys into a user-facing answer or commit them to Git. The system still needs real curator-approved sources, exhibit IDs, and a stronger reviewer identity model. The current Coze Agent still needs mandatory release-path wiring and authentic platform traces.
