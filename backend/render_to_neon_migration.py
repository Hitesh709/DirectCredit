"""One-time migration of live Render Postgres data into Neon.

This module is intentionally opt-in via MIGRATE_RENDER_TO_NEON=true. It never
writes to the Render/source database. The Neon target must be empty for the
business tables; otherwise the migration aborts rather than risking duplicate
rows. Counts are logged, but no customer data or credentials are logged.
"""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import MetaData, create_engine, insert, inspect, text
from sqlalchemy.engine import Engine


SKIP_TABLES = {"alembic_version", "schema_migration_check"}


def _target_engine() -> Engine:
    url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("NEON_DATABASE_URL is required for Render-to-Neon migration")
    return create_engine(url, pool_pre_ping=True, future=True)


def _common_business_tables(source: Engine, target: Engine) -> list[str]:
    source_tables = set(inspect(source).get_table_names(schema="public"))
    target_tables = set(inspect(target).get_table_names(schema="public"))
    return sorted((source_tables & target_tables) - SKIP_TABLES)


def _assert_target_empty(target: Engine, tables: list[str]) -> None:
    with target.connect() as conn:
        non_empty: list[str] = []
        for table_name in tables:
            count = conn.execute(
                text(f'SELECT COUNT(*) FROM public."{table_name}"')
            ).scalar_one()
            if int(count) > 0:
                non_empty.append(f"{table_name}={count}")
        if non_empty:
            raise RuntimeError(
                "Refusing Render-to-Neon migration because target tables are not empty: "
                + ", ".join(non_empty)
            )


def _reset_sequences(conn: Any, tables: list[str]) -> None:
    for table_name in tables:
        columns = inspect(conn).get_columns(table_name, schema="public")
        for column in columns:
            column_name = column["name"]
            if column_name != "id":
                continue
            sequence = conn.execute(
                text("SELECT pg_get_serial_sequence(:qualified_table, :column_name)"),
                {
                    "qualified_table": f"public.{table_name}",
                    "column_name": column_name,
                },
            ).scalar_one_or_none()
            if not sequence:
                continue
            max_id = conn.execute(
                text(f'SELECT MAX("{column_name}") FROM public."{table_name}"')
            ).scalar_one()
            if max_id is None:
                continue
            conn.execute(
                text("SELECT setval(:sequence_name, :max_id, true)"),
                {"sequence_name": sequence, "max_id": int(max_id)},
            )


def migrate_render_to_neon() -> dict[str, int]:
    """Copy all common business rows from the Render DB to the empty Neon DB."""
    source = __import__("backend.database", fromlist=["engine"]).engine
    target = _target_engine()
    tables = _common_business_tables(source, target)
    if not tables:
        raise RuntimeError("No common business tables found between Render and Neon")

    _assert_target_empty(target, tables)

    source_meta = MetaData()
    target_meta = MetaData()
    source_meta.reflect(bind=source, schema="public", only=tables)
    target_meta.reflect(bind=target, schema="public", only=tables)

    # Use the target FK dependency order, while preserving the actual Render rows.
    ordered_tables = [t.name for t in target_meta.sorted_tables if t.name in tables]
    counts: dict[str, int] = {}

    with source.connect() as source_conn, target.begin() as target_conn:
        for table_name in ordered_tables:
            source_table = source_meta.tables[f"public.{table_name}"]
            target_table = target_meta.tables[f"public.{table_name}"]
            rows = source_conn.execute(source_table.select()).mappings().all()
            if not rows:
                counts[table_name] = 0
                continue

            target_columns = {c.name for c in target_table.columns}
            payload = [
                {key: value for key, value in row.items() if key in target_columns}
                for row in rows
            ]
            for start in range(0, len(payload), 500):
                target_conn.execute(insert(target_table), payload[start : start + 500])
            counts[table_name] = len(payload)

        _reset_sequences(target_conn, ordered_tables)

    source.dispose()
    target.dispose()
    return counts
