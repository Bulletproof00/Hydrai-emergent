import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.core.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False, default="binance")
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="spot")

    __table_args__ = (UniqueConstraint("symbol", "exchange", "type", name="uq_instrument"),)


class Candle(Base):
    __tablename__ = "candles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("instrument_id", "timeframe", "ts", name="uq_candle"),)


class FundingRate(Base):
    __tablename__ = "funding_rates"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)


class OpenInterest(Base):
    __tablename__ = "open_interest"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ts_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ts_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)


class SupervisorReport(Base):
    __tablename__ = "supervisor_reports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=False)
    supervisor_name: Mapped[str] = mapped_column(String(64), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    invalidation: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)


Index("ix_candles_lookup", Candle.instrument_id, Candle.timeframe, Candle.ts)
Index("ix_findings_payload_gin", Finding.payload_json, postgresql_using="gin")
Index("ix_supervisor_payload_gin", SupervisorReport.payload_json, postgresql_using="gin")
