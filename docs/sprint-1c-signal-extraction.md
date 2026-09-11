# Sprint 1C - Structured epidemiological signal extraction

## Goal

Convert a stored `raw_item_payload` into validated, auditable atomic One Health signals. The LLM never writes directly to `signals`: it returns strict JSON, OETI validates it, resolves catalogs, and persists the result transactionally.

## New database object

Migration `20260910183000_signal_extraction_runs.sql` creates `public.extraction_runs` and links `public.signals.extraction_run_id` to the exact extraction run that produced each signal.

`extraction_runs` is server-only. It preserves provider/model/prompt/schema versions, response ID, original structured output, warnings, failures, and input size.

## Provider

Sprint 1C includes an OpenAI Responses API adapter using Structured Outputs with the repository JSON Schema. The provider is configurable through environment variables and can be replaced later without changing the persistence layer.

Recommended starting model for the MVP: `gpt-5.4-mini`. It can be overridden with `LLM_MODEL`.

## Environment

Add to the root `.env` (never commit it):

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-mini
LLM_API_KEY=YOUR_SERVER_SIDE_API_KEY
```

## Install updated worker

```powershell
cd C:\Proyectos\OETI\oeti
.\.venv\Scripts\Activate.ps1
pip install -e ".\services\worker[test]"
pytest .\services\worker\tests
```

## Apply database migration

First simulate:

```powershell
npx supabase db push --dry-run
```

Only `20260910183000_signal_extraction_runs.sql` should be pending. Then:

```powershell
npx supabase db push
npx supabase migration list
```

## First safe extraction: no persistence

Use the already validated MV Hondius raw item first:

```powershell
python -m onehealth_worker extract-raw-item `
  --raw-item-id "af424964-8b72-489b-b6bc-ea7d6218aeb3" `
  --no-persist `
  --output ".\tmp\mv-hondius-first-extraction.json"
```

This calls the model and validates the result, but does not create `signals` or `extraction_runs`.

Validate again independently:

```powershell
python -m onehealth_worker validate-extraction `
  --file ".\tmp\mv-hondius-first-extraction.json"
```

Review the JSON before persistence. Verify that every signal is atomic, evidence excerpts occur literally in the source, uncertainty is preserved, and unsupported relations are not inferred.

## Persist an approved JSON

```powershell
python -m onehealth_worker persist-extraction `
  --file ".\tmp\mv-hondius-first-extraction.json" `
  --provider openai_reviewed `
  --model gpt-5.4-mini
```

Alternatively, once the extractor is trusted, omit `--no-persist` from `extract-raw-item` to validate and persist in one command.

## Database checks

```sql
select id, raw_item_id, provider, model_name, status, created_at
from public.extraction_runs
order by created_at desc;

select id, raw_item_id, local_signal_key, version, is_current,
       domains, signal_type, signal_summary, verification_status,
       extraction_confidence, review_status
from public.signals
order by created_at desc;

select s.local_signal_key, e.excerpt, e.document_locator
from public.signal_evidence e
join public.signals s on s.id = e.signal_id
order by s.created_at desc, e.created_at;
```

## Scientific safeguards implemented

- Source-only extraction: no external knowledge in the extraction prompt.
- Unknown is distinct from negative/refuted.
- Literal evidence excerpt required for every signal.
- No automatic causal, transmission, or genomic relationship unless explicitly supported by the source.
- Database catalog resolution is performed server-side rather than trusting model normalization blindly.
- Re-extraction creates a new signal version and preserves the previous one.
- Failed runs are auditable in `extraction_runs`.
- The raw structured model output is preserved server-side.

## Acceptance criteria

Sprint 1C is accepted when at least one MV Hondius `raw_item` produces a schema-valid extraction whose signals are manually judged correct, the approved JSON persists transactionally, every signal has evidence, and the database links the signals to one successful `extraction_run`.

The next sprint is 1D: normalize and evaluate the six MV Hondius documents as a corpus, establish a gold-standard review set, measure extraction errors, and only then enable automated event matching.
