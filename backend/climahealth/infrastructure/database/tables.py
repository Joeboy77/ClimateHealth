from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IncidentActionRow(Base):
    __tablename__ = "incident_actions"

    action_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    district_id: Mapped[str] = mapped_column(String(80), index=True)
    agency: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(20))
    source_condition: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    due_on: Mapped[date] = mapped_column(Date)
    assigned_by: Mapped[str] = mapped_column(String(120))
    assigned_by_role: Mapped[str] = mapped_column(String(160))
    assigned_on: Mapped[date] = mapped_column(Date)
    updated_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_by_agency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class ActionTransitionRow(Base):
    """Append-only. Rows are inserted and never updated or deleted."""

    __tablename__ = "action_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(ForeignKey("incident_actions.action_id"), index=True)
    district_id: Mapped[str] = mapped_column(String(80), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20))
    actor_name: Mapped[str] = mapped_column(String(120))
    actor_agency: Mapped[str] = mapped_column(String(20))
    actor_role: Mapped[str] = mapped_column(String(60))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CommunityReportRow(Base):
    __tablename__ = "community_reports"

    report_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    district_id: Mapped[str] = mapped_column(String(80), index=True)
    report_type: Mapped[str] = mapped_column(String(40), index=True)
    note: Mapped[str] = mapped_column(Text)
    photo_reference: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(120))
    submitted_on: Mapped[date] = mapped_column(Date)
    verification: Mapped[str] = mapped_column(String(20), default="pending")
    verified_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verified_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="routine")


class GuardianRow(Base):
    __tablename__ = "guardians"

    user_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    district_id: Mapped[str] = mapped_column(String(80), index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    completed_mission_ids: Mapped[str] = mapped_column(Text, default="")
    answered_question_ids: Mapped[str] = mapped_column(Text, default="")


class ClimateReadingRow(Base):
    """The last good reading for a district, so a feed outage is survivable.

    Open-Meteo enforces a daily request ceiling. Holding the cache only in memory
    means a restart during an outage leaves the platform with nothing to say,
    which is the one thing an early-warning system must not do.
    """

    __tablename__ = "climate_readings"

    district_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[str] = mapped_column(Text)
