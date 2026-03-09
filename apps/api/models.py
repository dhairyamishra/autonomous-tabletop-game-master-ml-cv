"""SQLAlchemy ORM models for persistence.

Stores: game sessions, official state snapshots, event log, battle logs.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    player_assignments: Mapped[dict] = mapped_column(JSON, default=dict)
    current_player: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    current_round: Mapped[int] = mapped_column(Integer, default=1)

    state_snapshots: Mapped[list["StateSnapshot"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    events: Mapped[list["EventRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    battle_logs: Mapped[list["BattleLog"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class StateSnapshot(Base):
    __tablename__ = "state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("game_sessions.id"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(30), nullable=False)  # "phase_end", "battle_resolved", etc.
    player: Mapped[str] = mapped_column(String(20), nullable=False)
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["GameSession"] = relationship(back_populates="state_snapshots")


class EventRecord(Base):
    __tablename__ = "event_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("game_sessions.id"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    state_version_before: Mapped[int] = mapped_column(Integer, nullable=False)
    state_version_after: Mapped[int] = mapped_column(Integer, nullable=False)
    event_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    session: Mapped["GameSession"] = relationship(back_populates="events")


class BattleLog(Base):
    __tablename__ = "battle_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("game_sessions.id"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    battle_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    zone_id: Mapped[str] = mapped_column(String(50), nullable=False)
    attacker: Mapped[str] = mapped_column(String(20), nullable=False)
    defender: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    rng_seed: Mapped[str] = mapped_column(String(64), nullable=False)
    rng_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    battle_input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["GameSession"] = relationship(back_populates="battle_logs")
