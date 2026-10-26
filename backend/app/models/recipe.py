from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.tag import Tag


class KidFriendly(StrEnum):
    YES = "yes"
    WITH_ADJUSTMENTS = "with_adjustments"
    NO = "no"


recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


def utcnow() -> datetime:
    """Current UTC time as a naive datetime: SQLite has no time-zone type, values are UTC by convention."""
    return datetime.now(UTC).replace(tzinfo=None)


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (CheckConstraint("effort BETWEEN 1 AND 3", name="effort_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nr: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(Text)
    effort: Mapped[int | None]
    time_minutes: Mapped[int | None]
    servings: Mapped[int | None]
    kid_friendly: Mapped[KidFriendly | None] = mapped_column(
        Enum(
            KidFriendly,
            name="kid_friendly",
            native_enum=False,
            create_constraint=True,
            # Store the lowercase values ("with_adjustments"), not the member names.
            values_callable=lambda members: [member.value for member in members],
        )
    )
    ingredients: Mapped[str | None] = mapped_column(Text)
    steps: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=func.current_timestamp()
    )

    # The database removes the links (ON DELETE CASCADE), see ADR-8 / design D7.
    tags: Mapped[list[Tag]] = relationship(
        secondary=recipe_tags, back_populates="recipes", lazy="selectin", passive_deletes=True
    )
