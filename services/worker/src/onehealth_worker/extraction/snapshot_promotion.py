"""Explicit transactional promotion; never infer fact identity from ordinals."""
from .schema import validate_extraction


def validate_promotion_request(expected_revision, actor, reason):
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a nonnegative integer.")
    if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValueError("Promotion requires actor and reason.")


def promote_snapshot(conn, *, raw_item_id, run_id, expected_revision, actor, reason):
    with conn.cursor() as cur:
        cur.execute("select id from public.raw_items where id=%s for update", (raw_item_id,))
        if not cur.fetchone():
            raise ValueError("Source document does not exist.")
        cur.execute("select run_id, revision from public.extraction_snapshot_heads where raw_item_id=%s", (raw_item_id,))
        head = cur.fetchone()
        revision = head["revision"] if head else 0
        previous_run = str(head["run_id"]) if head else None
        if revision != expected_revision:
            raise ValueError("Stale snapshot revision; reconcile before promotion.")
        cur.execute("select raw_item_id,status,snapshot_policy,output_json from public.extraction_runs where id=%s for update", (run_id,))
        candidate = cur.fetchone()
        if (not candidate or str(candidate["raw_item_id"]) != raw_item_id
                or candidate["status"] != "succeeded" or candidate["snapshot_policy"] != "document-v1"):
            raise ValueError("Run is not a complete candidate for this document.")
        payload = candidate["output_json"]
        validate_extraction(payload)
        if payload["document"]["raw_item_id"] != raw_item_id:
            raise ValueError("Candidate payload belongs to another document.")
        if not payload["signals"]:
            raise ValueError("Empty snapshot requires a separate confirmation policy.")
        cur.execute("select 1 from public.extraction_snapshot_promotions where run_id=%s", (run_id,))
        if cur.fetchone():
            raise ValueError("Run has already been promoted; no implicit historical replay.")
        cur.execute("select id,raw_item_id,local_signal_key,is_current from public.signals where extraction_run_id=%s for update", (run_id,))
        members = cur.fetchall()
        expected_keys = {s["local_signal_id"] for s in payload["signals"]}
        if (len(members) != len(payload["signals"]) or len(expected_keys) != len(members)
                or {s["local_signal_key"] for s in members} != expected_keys
                or any(str(s["raw_item_id"]) != raw_item_id or s["is_current"] for s in members)):
            raise ValueError("Candidate membership is incomplete or inconsistent.")
        cur.execute("select id,extraction_run_id,review_status,reviewed_by,reviewed_at from public.signals where raw_item_id=%s and is_current=true for update", (raw_item_id,))
        current = cur.fetchall()
        if (not head and current) or (head and {str(s["extraction_run_id"]) for s in current} != {previous_run}):
            raise ValueError("Legacy or mixed vigence requires explicit reconciliation.")
        if any(s["review_status"] != "pending" or s["reviewed_by"] or s["reviewed_at"] for s in current):
            raise ValueError("Human review requires reconciliation before replacement.")
        ids = [s["id"] for s in current + members]
        cur.execute("""select
            exists(select 1 from public.event_signals where signal_id=any(%s::uuid[]))
            or exists(select 1 from public.signal_relations
                where source_signal_id=any(%s::uuid[]) or target_signal_id=any(%s::uuid[])) as linked""", (ids, ids, ids))
        if cur.fetchone()["linked"]:
            raise ValueError("Persisted links require reconciliation before promotion.")
        cur.execute("update public.signals set is_current=false where raw_item_id=%s and is_current=true", (raw_item_id,))
        cur.execute("update public.signals set is_current=true where extraction_run_id=%s", (run_id,))
        cur.execute("""insert into public.extraction_snapshot_heads(raw_item_id,run_id,revision)
            values(%s,%s,%s) on conflict(raw_item_id) do update
            set run_id=excluded.run_id,revision=excluded.revision""", (raw_item_id, run_id, revision + 1))
        cur.execute("""insert into public.extraction_snapshot_promotions
            (raw_item_id,revision,previous_run_id,run_id,actor,reason) values(%s,%s,%s,%s,%s,%s)""",
            (raw_item_id, revision + 1, previous_run, run_id, actor.strip(), reason.strip()))
    return {"status": "promoted", "raw_item_id": raw_item_id, "run_id": run_id,
            "previous_run_id": previous_run, "revision": revision + 1}
