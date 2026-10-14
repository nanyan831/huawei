# Exhibit Seed JSON Format

Use this format to import verified exhibit records into the NK HistoryGuide SQLite database.

Before importing real museum data, review the file with `docs/real_exhibit_seed_review.md`. The backend can validate structure and source-reference presence, but it does not verify historical accuracy or generate missing historical content.

The seed file must be a UTF-8 JSON array. Each item must contain one exhibit object. Even a single exhibit must be wrapped in an array.

Required fields:

- `id`: stable exhibit id, unique across the database
- `name`: exhibit name
- `description`: verified exhibit description or background summary
- `period`: historical period or exhibition section
- `keywords`: array of search and RAG metadata terms
- `importance`: integer from 1 to 5
- `source_reference`: source note, citation, or museum material reference

Optional metadata fields:

- `people`: related people
- `time_range`: related time span
- `themes`: thematic tags

Example:

```json
[
  {
    "id": "verified-exhibit-id",
    "name": "Verified Exhibit Name",
    "description": "Use only verified museum source text or curated summaries.",
    "period": "Verified Period",
    "keywords": ["keyword-a", "keyword-b"],
    "importance": 3,
    "people": [],
    "time_range": null,
    "themes": ["theme-a"],
    "source_reference": "Museum source, archive id, or GeniOS knowledge base reference."
  }
]
```

Do not import invented historical facts. Development fixtures must remain clearly marked as non-historical.

Validate a seed file before importing:

```powershell
python scripts\import_exhibits.py --dry-run data\example_exhibits.fixture.json
```

Expected success output:

```text
Validated 1 exhibit records. No records were imported.
```

The dry run validates JSON shape, required fields, `importance`, non-empty `source_reference`, duplicate ids inside the seed file, and id conflicts with the current database. It does not write records.

Export current database records to the same seed-style JSON shape:

```powershell
python scripts\export_exhibits.py backups\exhibits.backup.json
```

Use export before resetting or migrating a database that contains verified museum records. Export preserves the structured exhibit fields; it does not verify historical accuracy or generate missing source text.
