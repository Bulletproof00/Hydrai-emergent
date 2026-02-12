"""init schema

Revision ID: 20260212_0001
Revises:
Create Date: 2026-02-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260212_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.UniqueConstraint("symbol", "exchange", "type", name="uq_instrument"),
    )

    op.create_table(
        "candles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.UniqueConstraint("instrument_id", "timeframe", "ts", name="uq_candle"),
    )
    op.create_index("ix_candles_lookup", "candles", ["instrument_id", "timeframe", "ts"])

    op.create_table(
        "funding_rates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
    )
    op.create_table(
        "open_interest",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("run_id", sa.String(length=36), primary_key=True),
        sa.Column("ts_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ts_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.run_id"), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
    )
    op.create_index("ix_findings_payload_gin", "findings", ["payload_json"], postgresql_using="gin")

    op.create_table(
        "supervisor_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.run_id"), nullable=False),
        sa.Column("supervisor_name", sa.String(length=64), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
    )
    op.create_index(
        "ix_supervisor_payload_gin",
        "supervisor_reports",
        ["payload_json"],
        postgresql_using="gin",
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.run_id"), nullable=False),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("invalidation", sa.Float(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("signals")
    op.drop_index("ix_supervisor_payload_gin", table_name="supervisor_reports")
    op.drop_table("supervisor_reports")
    op.drop_index("ix_findings_payload_gin", table_name="findings")
    op.drop_table("findings")
    op.drop_table("analysis_runs")
    op.drop_table("open_interest")
    op.drop_table("funding_rates")
    op.drop_index("ix_candles_lookup", table_name="candles")
    op.drop_table("candles")
    op.drop_table("instruments")
