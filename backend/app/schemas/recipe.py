from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import KidFriendly, Tag


class RecipeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nr: int
    name: str
    effort: int | None
    time_minutes: int | None
    kid_friendly: KidFriendly | None
    tags: list[str]

    @field_validator("tags", mode="before")
    @classmethod
    def tag_names_sorted(cls, tags: list[Tag]) -> list[str]:
        return sorted(tag.name for tag in tags)


class RecipeDetail(RecipeListItem):
    servings: int | None
    ingredients: str | None
    steps: str | None
    created_at: datetime
    updated_at: datetime
