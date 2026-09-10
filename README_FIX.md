# OETI Sprint 1B — duplicate metadata refresh v0.2.2

This patch keeps content-hash deduplication but changes duplicate handling:

- Same source + same normalized body stays one `raw_item` (`inserted: false`).
- Parser-derived metadata (`title`, `published_at`, `language`, `mime_type`, `url`) is refreshed on the existing row.
- `metadata.last_seen_at` records the latest fetch time.
- The Argentina.gob.ar title fix from v0.2.1 is included.

Copy the patch over the project root and reinstall the editable worker only if needed:

```powershell
pip install -e ".\services\worker[test]"
pytest .\services\worker\tests
```

Then rerun the same `ingest-url`. `inserted: false` is expected if the body did not change. Verify the row in Supabase; the title should now be corrected.
