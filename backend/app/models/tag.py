from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (CheckConstraint("name_key <> ''", name="name_key_not_empty"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Displayed spelling: trimmed, as first created.
    name: Mapped[str] = mapped_column(Text)
    # Case-folded name. SQLite's NOCASE and lower() only fold ASCII, so uniqueness
    # regardless of case (including umlauts) is enforced on this column instead.
    name_key: Mapped[str] = mapped_column(Text, unique=True)

    recipes: Mapped[list["Recipe"]] = relationship(
        secondary="recipe_tags", back_populates="tags", passive_deletes=True
    )

    @validates("name")
    def _normalize_name(self, _key: str, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Tag name must not be empty")
        self.name_key = name.casefold()
        return name
