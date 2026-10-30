from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Recipe
from app.schemas import RecipeListItem

router = APIRouter(prefix="/api/recipes")


@router.get("", response_model=list[RecipeListItem])
async def list_recipes(db: AsyncSession = Depends(get_db)) -> list[Recipe]:
    return list((await db.scalars(select(Recipe).order_by(Recipe.nr))).all())
