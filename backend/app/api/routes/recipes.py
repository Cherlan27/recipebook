from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Recipe
from app.schemas import RecipeDetail, RecipeListItem

router = APIRouter(prefix="/api/recipes")


@router.get("", response_model=list[RecipeListItem])
async def list_recipes(db: AsyncSession = Depends(get_db)) -> list[Recipe]:
    return list((await db.scalars(select(Recipe).order_by(Recipe.nr))).all())


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)) -> Recipe:
    recipe = await db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
