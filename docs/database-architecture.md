# Database Architecture

SQLite via SQLAlchemy 2.0's async ORM (`aiosqlite` driver). Models in `backend/app/db/models.py`.

## Schema

```
patients                          safety_reports                      audit_log_entries
─────────                         ───────────────                     ──────────────────
id (PK)                           id (PK)                             id (PK)
external_ref                      patient_id (FK → patients.id)       report_id (FK → safety_reports.id)
age                                raw_prescription_text               timestamp
weight_kg                          status                              agent
sex                                 overall_severity                    action
allergies (JSON list)              retry_count                        detail (JSON)
conditions (JSON list)              pharmacist_review_flag
renal_function                     medications (JSON)
hepatic_function                   findings (JSON)
created_at                         summary
                                    error
                                    created_at
                                    completed_at
```

`Patient` 1—N `SafetyReport` 1—N `AuditLogEntry`.

## Why JSON columns for medications/findings

`medications` and `findings` are stored as JSON blobs on the `SafetyReport` row rather than
normalized into their own tables. This is a deliberate simplification: they're written once
(when the graph finishes) and read as a unit (the report page always wants all of them
together, never "give me just this one finding across all reports"). Normalizing them would
add join complexity with no corresponding query benefit at this project's scale. If a future
requirement needed cross-report finding queries (e.g. "show me every contraindicated finding
across all reports this month"), that would be the trigger to normalize.

## Single-writer constraint

SQLite serializes writes at the file level. That's fine for this project's deployment model
(one backend process) and is called out explicitly in `docs/deployment.md` — it's the reason
the progress broadcaster is in-process rather than a shared queue, and it's the first thing
that would need to change (e.g. to Postgres) before running multiple backend replicas.
