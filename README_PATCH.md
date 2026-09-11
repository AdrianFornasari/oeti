# OETI Sprint 1C semantic refinement v0.3.4

Copy the CONTENTS of this package into the OETI repository root.

Then run:

```powershell
python -m pytest .\services\worker\tests
npx supabase db push --dry-run
```

The dry-run must show only `20260911160000_signal_semantics_v03.sql`. Do not persist a new extraction until the migration is applied and the `--no-persist` JSON has been reviewed.
