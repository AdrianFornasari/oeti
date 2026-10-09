"""Operational cohort planning within a database-enforced read-only snapshot."""
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .event_creation_planner_v049 import EventCreationPlanner
from .event_matching_repository_v049 import EventMatchingRepository


def plan_event_creation_cohorts(
    database_url: str, signal_relation_ids: list[str],
) -> dict[str, Any]:
    repository = EventMatchingRepository(database_url)
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10) as connection:
        connection.read_only = True
        connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ

        @contextmanager
        def snapshot_connection():
            yield connection

        repository.connection = snapshot_connection
        return EventCreationPlanner(repository).plan_cohorts(signal_relation_ids)
