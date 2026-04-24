from datetime import datetime, timezone
from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.database import Base


class User(Base):
    """User model for storing registered users (admins and employees)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="employee")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    strikes_received: Mapped[List["Strike"]] = relationship(
        "Strike", foreign_keys="Strike.user_id", back_populates="user"
    )
    strikes_given: Mapped[List["Strike"]] = relationship(
        "Strike", foreign_keys="Strike.given_by_id", back_populates="given_by"
    )
    pizza_events: Mapped[List["PizzaEvent"]] = relationship(
        "PizzaEvent", back_populates="triggered_by"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'employee')", name="ck_users_role"),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"


class Strike(Base):
    """Strike model for storing strike records issued to employees."""

    __tablename__ = "strikes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    given_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="strikes_received"
    )
    given_by: Mapped["User"] = relationship(
        "User", foreign_keys=[given_by_id], back_populates="strikes_given"
    )
    pizza_events: Mapped[List["PizzaEvent"]] = relationship(
        "PizzaEvent",
        secondary="pizza_event_strikes",
        back_populates="strikes",
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('late', 'bug', 'forgot_meeting', 'dress_code', 'other')",
            name="ck_strikes_category",
        ),
        Index("idx_strikes_user_id", "user_id"),
        Index("idx_strikes_given_by_id", "given_by_id"),
        Index("idx_strikes_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Strike(id={self.id}, user_id={self.user_id}, category={self.category})>"


class PizzaEvent(Base):
    """PizzaEvent model for storing pizza party events triggered when users hit 3 strikes."""

    __tablename__ = "pizza_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    triggered_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    triggered_by: Mapped["User"] = relationship(
        "User", back_populates="pizza_events"
    )
    strikes: Mapped[List["Strike"]] = relationship(
        "Strike",
        secondary="pizza_event_strikes",
        back_populates="pizza_events",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'scheduled', 'completed', 'cancelled')",
            name="ck_pizza_events_status",
        ),
        Index("idx_pizza_events_triggered_by", "triggered_by_id"),
        Index("idx_pizza_events_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PizzaEvent(id={self.id}, triggered_by_id={self.triggered_by_id}, status={self.status})>"


class PizzaEventStrike(Base):
    """Join table linking pizza events to the strikes that triggered them."""

    __tablename__ = "pizza_event_strikes"

    pizza_event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pizza_events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    strike_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strikes.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Notification(Base):
    """Notification model for storing user notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_is_read", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"
