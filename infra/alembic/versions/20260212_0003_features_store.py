"""feature store tables

Revision ID: 20260212_0003
Revises: 20260212_0002
Create Date: 2026-02-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260212_0003"
down_revision: Union[str, None] = "20260212_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=True),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("feature_key", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("indicator_type", sa.String(length=32), nullable=True),
        sa.Column("params_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("formula_expr", sa.Text(), nullable=True),
        sa.Column("output_schema_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("config_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "feature_definition_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("feature_definition_id", sa.Integer(), sa.ForeignKey("feature_definitions.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "feature_values",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("feature_definition_id", sa.Integer(), sa.ForeignKey("feature_definitions.id"), nullable=False),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_num", sa.Float(), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("value_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("feature_definition_id", "instrument_id", "timeframe", "ts", name="uq_feature_value"),
    )
    op.create_index(
        "ix_feature_values_lookup",
        "feature_values",
        ["feature_definition_id", "instrument_id", "timeframe", "ts"],
    )
    op.create_table(
        "feature_compute_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("feature_definition_id", sa.Integer(), sa.ForeignKey("feature_definitions.id"), nullable=False),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feature_compute_runs")
    op.drop_index("ix_feature_values_lookup", table_name="feature_values")
    op.drop_table("feature_values")
    op.drop_table("feature_definition_versions")
    op.drop_table("feature_definitions")
