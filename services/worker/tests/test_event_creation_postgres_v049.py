"""Opt-in integration suite against the disposable localhost cluster only.

OETI_LOCAL_PG_TESTS=1 enables tests on 127.0.0.1:55449, user oeti_test.
Each test creates and drops its own oeti_test_* database. No production DSN
is read. Relevant DDL is taken verbatim from the checked-in migrations.
"""
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.types.json import Jsonb

from onehealth_worker.evaluation.event_creation_v049 import build_event_creation_cohort_seed
from onehealth_worker.evaluation.event_creation_planner_v049 import EventCreationPlanner
from onehealth_worker.evaluation.event_matching_repository_v049 import EventMatchingRepository

pytestmark = pytest.mark.skipif(os.environ.get("OETI_LOCAL_PG_TESTS") != "1", reason="Disposable localhost PostgreSQL not enabled")
ADMIN = "host=127.0.0.1 port=55449 user=oeti_test dbname=postgres connect_timeout=5"


@pytest.fixture
def cohort():
    name = "oeti_test_" + uuid4().hex
    with psycopg.connect(ADMIN, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(name)))
    dsn = f"host=127.0.0.1 port=55449 user=oeti_test dbname={name} connect_timeout=5"
    try:
        root = Path(__file__).resolve().parents[3]
        migration = (root / "supabase/migrations/20260910090000_initial_core_schema.sql").read_text(encoding="utf-8")
        tables = ("sources", "raw_items", "raw_item_payloads", "diseases", "pathogens", "signals", "signal_evidence", "events", "event_signals", "signal_relations")
        with psycopg.connect(dsn) as conn:
            conn.execute("create schema auth; create table auth.users(id uuid primary key)")
            for ddl in re.findall(r"create type public\.\w+ as enum \(.*?\);", migration, re.S):
                conn.execute(ddl)
            for table in tables:
                ddl = re.search(rf"create table public\.{table} \(.*?\n\);", migration, re.S)
                assert ddl, table
                conn.execute(ddl.group())
            conn.execute(re.search(r"create or replace function public.set_updated_at\(\).*?\$\$;", migration, re.S).group())
            for ddl in re.findall(r"create trigger \w+\s+.*?execute function public.set_updated_at\(\);", migration, re.S):
                if any(f"on public.{table}\n" in ddl for table in tables):
                    conn.execute(ddl)
            eligibility = (root / "supabase/migrations/20260911190000_diagnostics_matching_v035.sql").read_text(encoding="utf-8")
            conn.execute(re.search(r"alter table public.signals\s+add column event_matching_eligible.*?;", eligibility, re.S).group())
            source = uuid4()
            pathogen = uuid4()
            raw_ids = [uuid4(), uuid4()]
            ids = [uuid4() for _ in range(5)]
            relation_ids = [uuid4() for _ in range(3)]
            conn.execute("insert into public.sources(id,code,name,kind,ingestion) values(%s,'test','test','primary_official','manual')", (source,))
            conn.execute("insert into public.pathogens(id,canonical_name) values(%s,'Andes virus')", (pathogen,))
            excerpt = "Se investiga el brote en el buque MV Hondius."
            for index, raw_id in enumerate(raw_ids):
                conn.execute("insert into public.raw_items(id,source_id,url,content_sha256,published_at) values(%s,%s,'https://example.test',%s,'2026-05-04T18:06:44Z')", (raw_id, source, str(index)))
                conn.execute("insert into public.raw_item_payloads(raw_item_id,raw_text) values(%s,%s)", (raw_id, excerpt))
            for index, identifier in enumerate(ids):
                conn.execute("""insert into public.signals(id,raw_item_id,local_signal_key,signal_type,signal_summary,extraction_confidence,pathogen_id,domains,occurred_start)
                    values(%s,%s,%s,'case_report','test',0.8,%s,ARRAY['human']::public.one_health_domain[],'2026-05-02')""", (identifier, raw_ids[index % 2], str(index), pathogen))
                conn.execute("insert into public.signal_evidence(signal_id,evidence_type,excerpt) values(%s,'quote',%s)", (identifier, excerpt))
            pairs = [(0, 1), (1, 2), (3, 4)]
            rationale = {"producer": "oeti_event_matcher", "gate": "eligible", "decision": "auto_linked", "merge_allowed": True,
                "information_coverage": 0.15,
                "matcher_version": "0.4.8", "policy_version": "0.4.9", "context_resolver_version": "0.4.9",
                "auto_link_guard_override_reason": "shared_strong_event_context_anchor", "shared_event_context_anchors": ["vessel:mv hondius"]}
            for relation_id, (a, b) in zip(relation_ids, pairs):
                conn.execute("insert into public.signal_relations(id,source_signal_id,target_signal_id,relation,rationale) values(%s,%s,%s,'refines',%s)", (relation_id, ids[a], ids[b], Jsonb(rationale)))
        repo = EventMatchingRepository(dsn, event_creation_writes_enabled=True)
        seed = build_event_creation_cohort_seed(signals=[repo.load_event_creation_signal(str(i)) for i in ids],
            relations=[repo.load_persisted_matcher_relation_by_id(str(i)) for i in relation_ids], strong_event_context_anchors=["vessel:mv hondius"])
        yield repo, seed, ids, relation_ids
    finally:
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            admin.execute(sql.SQL("drop database {} with (force)").format(sql.Identifier(name)))


def counts(repo):
    with repo.connection() as conn:
        return conn.execute("select (select count(*) from public.events) as events, (select count(*) from public.event_signals) as memberships").fetchone()


def snapshot(repo):
    with repo.connection() as conn:
        return conn.execute("select (select jsonb_agg(e order by id) from public.events e) as events, (select jsonb_agg(es order by signal_id) from public.event_signals es) as memberships").fetchone()


def test_postgres_creation_replay_and_read_only_dry_run(cohort):
    repo, seed, _, relation_ids = cohort
    assert seed["domains_present"] == ["human"]
    before = snapshot(repo)
    assert repo.persist_event_creation_cohort(event_seed=seed)["status"] == "ready_to_create"
    assert snapshot(repo) == before
    planner = EventCreationPlanner(repo)
    relation_refs = [str(identifier) for identifier in relation_ids]
    planned = planner.plan_cohorts(relation_refs)
    assert planned["summary"] == {"ready_to_create": 1, "already_exists": 0, "blocked": 0}
    assert planned["cohorts"][0]["event_seed"] == seed
    assert snapshot(repo) == before
    created = repo.persist_event_creation_cohort(event_seed=seed, dry_run=False)
    assert created["status"] == "created"
    assert list(counts(repo).values()) == [1, 5]
    after = snapshot(repo)
    replay_plan = planner.plan_cohorts(relation_refs)
    assert replay_plan["summary"] == {"ready_to_create": 0, "already_exists": 1, "blocked": 0}
    assert snapshot(repo) == after
    for dry_run in (True, False):
        replay = repo.persist_event_creation_cohort(event_seed=seed, dry_run=dry_run)
        assert replay["status"] == "already_exists"
        assert replay["event_id"] == created["event_id"]
        assert snapshot(repo) == after


@pytest.mark.parametrize("change", ["ineligible", "stale", "relation", "manual", "other", "closed", "raw_text", "version", "coverage_missing", "override_removed"])
def test_postgres_revalidates_after_planning(cohort, change):
    repo, seed, ids, relation_ids = cohort
    assert repo.persist_event_creation_cohort(event_seed=seed)["status"] == "ready_to_create"
    with repo.connection() as conn:
        if change in {"ineligible", "stale"}:
            field = "event_matching_eligible" if change == "ineligible" else "is_current"
            conn.execute(sql.SQL("update public.signals set {}=false where id=%s").format(sql.Identifier(field)), (ids[0],))
        elif change == "relation":
            conn.execute("update public.signal_relations set hard_conflict=true where id=%s", (relation_ids[0],))
        elif change == "raw_text":
            conn.execute("update public.raw_item_payloads set raw_text='unrelated document'")
        elif change == "version":
            conn.execute("update public.signal_relations set rationale=jsonb_set(rationale,'{policy_version}','\"0.4.8\"') where id=%s", (relation_ids[0],))
        elif change in {"coverage_missing", "override_removed"}:
            key = "information_coverage" if change == "coverage_missing" else "auto_link_guard_override_reason"
            conn.execute("update public.signal_relations set rationale=rationale - %s where id=%s", (key, relation_ids[0]))
        else:
            code = seed["event_code"] if change == "closed" else "other"
            event_id = conn.execute("insert into public.events(event_code,title,lifecycle_status) values(%s,'test',%s) returning id", (code, "closed" if change == "closed" else "active")).fetchone()["id"]
            if change != "closed":
                conn.execute("insert into public.event_signals(event_id,signal_id,match_decision) values(%s,%s,%s)", (event_id, ids[0], "manual_unlinked" if change == "manual" else "auto_linked"))
    before = snapshot(repo)
    result = repo.persist_event_creation_cohort(event_seed=seed, dry_run=False)
    assert result["status"] == "blocked"
    assert result["dry_run"] is False
    if change in {"coverage_missing", "override_removed"}:
        assert result["reason"] == "invalid_matcher_policy"
    assert snapshot(repo) == before


def test_postgres_membership_failure_rolls_back_everything(cohort):
    repo, seed, _, _ = cohort
    with repo.connection() as conn:
        conn.execute("""create function public.fail_membership() returns trigger language plpgsql as $$
            begin
              if (select count(*) from public.event_signals) >= 2 then
                raise exception 'injected membership failure';
              end if;
              return new;
            end $$;
            create trigger test_failure before insert on public.event_signals
            for each row execute function public.fail_membership();""")
    before = snapshot(repo)
    with pytest.raises(psycopg.errors.RaiseException, match="injected membership failure"):
        repo.persist_event_creation_cohort(event_seed=seed, dry_run=False)
    assert snapshot(repo) == before
    assert list(counts(repo).values()) == [0, 0]


def test_postgres_concurrent_creation_is_idempotent(cohort):
    repo, seed, _, _ = cohort
    barrier = Barrier(2)
    def run():
        barrier.wait(timeout=10)
        return repo.persist_event_creation_cohort(event_seed=seed, dry_run=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert sorted(row["status"] for row in results) == ["already_exists", "created"]
    assert len({row["event_id"] for row in results}) == 1
    assert list(counts(repo).values()) == [1, 5]


def test_postgres_noncooperating_writer_cannot_change_validation_inputs(cohort):
    repo, seed, ids, _ = cohort
    locked, release = Event(), Event()
    original = repo._validate_event_creation_cohort
    def validate(cur, **kwargs):
        locked.set()
        assert release.wait(timeout=10)
        return original(cur, **kwargs)
    repo._validate_event_creation_cohort = validate
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(repo.persist_event_creation_cohort, event_seed=seed, dry_run=False)
        try:
            assert locked.wait(timeout=10)
            with pytest.raises(psycopg.errors.LockNotAvailable):
                with repo.connection() as conn:
                    conn.execute("set local lock_timeout = '300ms'")
                    conn.execute("update public.signals set event_matching_eligible=false where id=%s", (ids[0],))
        finally:
            release.set()
        assert future.result(timeout=10)["status"] == "created"
    assert list(counts(repo).values()) == [1, 5]


@pytest.mark.parametrize("separate_anchor", [False, True])
def test_postgres_direct_creation_blocks_multiple_cohorts(cohort, separate_anchor):
    repo, original_seed, ids, relation_ids = cohort
    anchors = ["vessel:mv hondius", "vessel:mv ortelius"] if separate_anchor else []
    with repo.connection() as conn:
        if separate_anchor:
            excerpt = "Se investiga el brote en el buque MV Ortelius."
            conn.execute("update public.raw_item_payloads set raw_text=raw_text || %s", ("\n\n" + excerpt,))
            conn.execute("update public.signal_evidence set excerpt=%s where signal_id=any(%s::uuid[])", (excerpt, ids[3:]))
            conn.execute("update public.signal_relations set rationale=jsonb_set(rationale,'{shared_event_context_anchors}',%s) where id=%s", (Jsonb(["vessel:mv ortelius"]), relation_ids[2]))
        else:
            conn.execute("update public.signal_relations set rationale=(rationale - 'auto_link_guard_override_reason') || %s", (Jsonb({"shared_event_context_anchors": [], "information_coverage": 0.8}),))
    seed = build_event_creation_cohort_seed(
        signals=[repo.load_event_creation_signal(str(identifier)) for identifier in ids],
        relations=[repo.load_persisted_matcher_relation_by_id(str(identifier)) for identifier in relation_ids],
        strong_event_context_anchors=anchors,
    )
    assert seed["event_code"] == original_seed["event_code"]
    before = snapshot(repo)
    for dry_run in (True, False):
        result = repo.persist_event_creation_cohort(event_seed=seed, dry_run=dry_run)
        assert result["status"] == "blocked"
        assert result["reason"] == "multiple_event_creation_cohorts"
        assert result["cohort_count"] == 2
        assert snapshot(repo) == before
