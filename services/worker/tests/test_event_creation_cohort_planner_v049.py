import pytest

from onehealth_worker.evaluation.event_creation_planner_v049 import EventCreationPlanner


def relation(identifier, source, target, *, anchor="vessel:mv hondius", decision="auto_linked"):
    return {"signal_relation_id": identifier, "source_signal_id": source,
        "target_signal_id": target, "matcher_version": "0.4.8", "matcher_result": {
            "gate": "eligible", "decision": decision, "merge_allowed": True,
            "hard_conflict": False, "relation": "refines", "score": 0.9,
            "shared_event_context_anchors": [anchor] if anchor else [],
        }}


class Repository:
    def __init__(self, relations, *, status="ready_to_create", stale=None):
        self.relations = {row["signal_relation_id"]: row for row in relations}
        self.status = status
        self.stale = stale
        self.reads = []
        self.validations = []
    def load_persisted_matcher_relation_by_id(self, identifier):
        self.reads.append(identifier)
        return self.relations[identifier]
    def load_event_creation_signal(self, identifier):
        if identifier == self.stale: raise ValueError("signal no longer eligible")
        return {"signal_id": identifier, "domains": ["human"]}
    def persist_event_creation_cohort(self, *, event_seed, dry_run):
        assert dry_run is True
        self.validations.append(event_seed)
        return {"status": self.status, "dry_run": True, "event_seed": event_seed,
            "event_id": "existing" if self.status == "already_exists" else None}


@pytest.mark.parametrize("status", ["ready_to_create", "already_exists", "blocked"])
def test_cohort_planner_groups_context_and_delegates_only_to_dry_run(status):
    repo = Repository([relation("r1", "a", "b"), relation("r2", "c", "d")], status=status)
    report = EventCreationPlanner(repo).plan_cohorts(["r2", "r1", "r2"])
    assert report["mode"] == "plan_only"
    assert report["summary"][status] == 1
    assert len(report["cohorts"]) == 1
    assert repo.reads == ["r1", "r2"]
    assert repo.validations[0]["source_signal_ids"] == ["a", "b", "c", "d"]
    assert repo.validations[0]["source_relation_ids"] == ["r1", "r2"]
    assert report["cohorts"][0]["validation"]["status"] == status


def test_cohort_planner_keeps_unrelated_cohorts_separate():
    repo = Repository([relation("r1", "a", "b", anchor=None), relation("r2", "c", "d", anchor=None)])
    report = EventCreationPlanner(repo).plan_cohorts(["r1", "r2"])
    assert len(report["cohorts"]) == 2
    assert len(repo.validations) == 2


@pytest.mark.parametrize("field,value", [("gate", "ineligible"), ("decision", "review_required"),
    ("decision", "rejected"), ("hard_conflict", True), ("merge_allowed", False), ("relation", "possibly_related")])
def test_cohort_planner_reports_excluded_relations(field, value):
    row = relation("r1", "a", "b")
    row["matcher_result"][field] = value
    repo = Repository([row])
    report = EventCreationPlanner(repo).plan_cohorts(["r1"])
    assert report["excluded_relation_ids"] == ["r1"]
    assert report["cohorts"] == []
    assert repo.validations == []


def test_cohort_planner_blocks_stale_signal_and_continues_other_cohort():
    repo = Repository([relation("r1", "a", "b", anchor=None), relation("r2", "c", "d", anchor=None)], stale="a")
    report = EventCreationPlanner(repo).plan_cohorts(["r1", "r2"])
    assert report["summary"] == {"ready_to_create": 1, "already_exists": 0, "blocked": 1}
    blocked = next(item for item in report["cohorts"] if item["validation"]["status"] == "blocked")
    assert blocked["validation"]["reason"] == "invalid_cohort_seed"
    assert len(repo.validations) == 1


def test_empty_cohort_plan_does_not_access_repository():
    repo = Repository([])
    report = EventCreationPlanner(repo).plan_cohorts([])
    assert report["cohorts"] == []
    assert repo.reads == []
