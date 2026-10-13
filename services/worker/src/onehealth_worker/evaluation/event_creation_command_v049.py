"""Operational cohort planning within a database-enforced read-only snapshot."""
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .event_creation_planner_v049 import EventCreationPlanner
from .event_creation_executor_v049 import EventCreationExecutor
from .event_matching_repository_v049 import EventMatchingRepository


@contextmanager
def _read_only_repository(database_url: str):
    repository = EventMatchingRepository(database_url)
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10) as connection:
        connection.read_only = True
        connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ

        @contextmanager
        def snapshot_connection():
            yield connection

        repository.connection = snapshot_connection
        yield repository


def plan_event_creation_cohorts(
    database_url: str, signal_relation_ids: list[str],
) -> dict[str, Any]:
    with _read_only_repository(database_url) as repository:
        return EventCreationPlanner(repository).plan_cohorts(signal_relation_ids)


def validate_event_creation_plan(
    database_url: str, report: dict[str, Any], expected_event_code: str,
) -> dict[str, Any]:
    with _read_only_repository(database_url) as repository:
        return EventCreationExecutor(repository).execute_planned_cohort(
            report=report, expected_event_code=expected_event_code, dry_run=True,
        )
