import unicodedata
from datetime import UTC, datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models import KidFriendly, Recipe, Tag

pytestmark = pytest.mark.anyio


async def test_recipes_with_tags_are_stored_and_read_back(db_session):
    soup = Tag(name="Soup")
    quick = Tag(name="Quick")
    vegetarian = Tag(name="Vegetarian")
    db_session.add_all(
        [
            Recipe(
                nr=1,
                name="Tomato soup",
                effort=1,
                time_minutes=30,
                servings=4,
                kid_friendly=KidFriendly.YES,
                ingredients="1 kg tomatoes\n1 onion\n500 ml stock",
                steps="Chop everything\nSimmer for 20 minutes\nBlend",
                tags=[soup, quick, vegetarian],
            ),
            Recipe(
                nr=2,
                name="Spicy curry",
                effort=3,
                time_minutes=60,
                servings=2,
                kid_friendly=KidFriendly.WITH_ADJUSTMENTS,
                ingredients="rice\ncurry paste",
                steps="Cook rice\nFry paste",
                tags=[vegetarian],
            ),
            Recipe(
                nr=3,
                name="Liver",
                effort=2,
                time_minutes=20,
                servings=1,
                kid_friendly=KidFriendly.NO,
                ingredients="liver",
                steps="Fry",
                tags=[quick, soup],
            ),
        ]
    )
    await db_session.commit()
    db_session.expunge_all()

    recipes = (await db_session.scalars(select(Recipe).order_by(Recipe.nr))).all()

    assert [r.name for r in recipes] == ["Tomato soup", "Spicy curry", "Liver"]
    first = recipes[0]
    assert (first.effort, first.time_minutes, first.servings) == (1, 30, 4)
    assert first.kid_friendly is KidFriendly.YES
    assert first.ingredients.splitlines() == ["1 kg tomatoes", "1 onion", "500 ml stock"]
    assert first.steps.splitlines() == ["Chop everything", "Simmer for 20 minutes", "Blend"]
    assert {t.name for t in first.tags} == {"Soup", "Quick", "Vegetarian"}
    assert recipes[1].kid_friendly is KidFriendly.WITH_ADJUSTMENTS
    assert {t.name for t in recipes[1].tags} == {"Vegetarian"}
    assert recipes[2].kid_friendly is KidFriendly.NO
    assert {t.name for t in recipes[2].tags} == {"Quick", "Soup"}


async def test_migrated_database_matches_data_model(db_session):
    def differences(sync_connection):
        return compare_metadata(MigrationContext.configure(sync_connection), Base.metadata)

    connection = await db_session.connection()
    assert await connection.run_sync(differences) == []


async def test_recipe_with_only_required_fields(db_session):
    db_session.add(Recipe(nr=7, name="Plain"))
    await db_session.commit()
    db_session.expunge_all()

    recipe = await db_session.scalar(select(Recipe))

    assert (recipe.nr, recipe.name) == (7, "Plain")
    assert recipe.effort is None
    assert recipe.time_minutes is None
    assert recipe.servings is None
    assert recipe.kid_friendly is None
    assert recipe.ingredients is None
    assert recipe.steps is None
    assert recipe.tags == []


async def test_recipe_without_number_is_rejected(db_session):
    db_session.add(Recipe(name="No number"))

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_recipe_without_name_is_rejected(db_session):
    db_session.add(Recipe(nr=1))

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_duplicate_recipe_number_is_rejected(db_session):
    db_session.add(Recipe(nr=12, name="Original"))
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await db_session.execute(text("INSERT INTO recipes (nr, name) VALUES (12, 'Copy')"))
    await db_session.rollback()

    recipes = (await db_session.scalars(select(Recipe))).all()
    assert [(r.nr, r.name) for r in recipes] == [(12, "Original")]


async def test_effort_within_range_is_accepted(db_session):
    db_session.add_all([Recipe(nr=i, name=f"Effort {i}", effort=i) for i in (1, 2, 3)])
    await db_session.commit()

    efforts = (await db_session.scalars(select(Recipe.effort).order_by(Recipe.nr))).all()
    assert efforts == [1, 2, 3]


@pytest.mark.parametrize("effort", [0, 4])
async def test_effort_out_of_range_is_rejected(db_session, effort):
    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("INSERT INTO recipes (nr, name, effort) VALUES (1, 'Bad', :effort)"),
            {"effort": effort},
        )


async def test_defined_kid_friendly_values_are_accepted(db_session):
    db_session.add_all(
        [Recipe(nr=i, name=value.value, kid_friendly=value) for i, value in enumerate(KidFriendly)]
    )
    await db_session.commit()

    stored = (await db_session.execute(text("SELECT kid_friendly FROM recipes ORDER BY nr"))).scalars().all()
    assert stored == ["yes", "with_adjustments", "no"]
    db_session.expunge_all()
    recipes = (await db_session.scalars(select(Recipe).order_by(Recipe.nr))).all()
    assert [r.kid_friendly for r in recipes] == list(KidFriendly)


async def test_undefined_kid_friendly_value_is_rejected(db_session):
    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("INSERT INTO recipes (nr, name, kid_friendly) VALUES (1, 'Bad', 'maybe')")
        )


async def test_timestamps_are_set_on_creation(db_session):
    recipe = Recipe(nr=1, name="Fresh")
    before = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(recipe)
    await db_session.commit()
    after = datetime.now(UTC).replace(tzinfo=None)

    assert before <= recipe.created_at <= after
    assert before <= recipe.updated_at <= after


async def test_updated_at_advances_when_recipe_is_changed(db_session):
    # Stored in the past so the assertion does not depend on the clock ticking between two commits
    stored_at = datetime(2020, 1, 1, 12, 0, 0)
    recipe = Recipe(nr=1, name="Before", created_at=stored_at, updated_at=stored_at)
    db_session.add(recipe)
    await db_session.commit()
    created_at, updated_before = recipe.created_at, recipe.updated_at

    recipe.name = "After"
    await db_session.commit()

    assert recipe.updated_at > updated_before
    assert recipe.created_at == created_at


async def test_tag_name_is_trimmed(db_session):
    db_session.add(Tag(name="  Pasta  "))
    await db_session.commit()

    assert await db_session.scalar(select(Tag.name)) == "Pasta"


@pytest.mark.parametrize(
    ("stored", "duplicate"),
    [
        ("Pasta", "pasta"),
        ("Pasta", " PASTA "),
        ("Österreichisch", "österreichisch"),
        # The same visible text in different Unicode forms (macOS input, copy-paste from PDFs).
        (unicodedata.normalize("NFC", "Österreichisch"), unicodedata.normalize("NFD", "Österreichisch")),
        (unicodedata.normalize("NFD", "Österreichisch"), unicodedata.normalize("NFC", "österreichisch")),
        # casefold() deliberately treats ß as ss.
        ("Maße", "Masse"),
        ("Masse", "MAßE"),
    ],
)
async def test_tag_names_are_unique_regardless_of_case(db_session, stored, duplicate):
    db_session.add(Tag(name=stored))
    await db_session.commit()

    db_session.add(Tag(name=duplicate))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    assert (await db_session.scalars(select(Tag.name))).all() == [unicodedata.normalize("NFC", stored)]


def test_tag_name_is_stored_in_composed_unicode_form():
    tag = Tag(name=unicodedata.normalize("NFD", " Österreichisch "))

    assert tag.name == "Österreichisch"
    assert unicodedata.is_normalized("NFC", tag.name)


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_tag_name_is_rejected(name):
    with pytest.raises(ValueError):
        Tag(name=name)


async def test_one_tag_on_several_recipes(db_session):
    vegetarian = Tag(name="Vegetarian")
    db_session.add_all(
        [Recipe(nr=1, name="A", tags=[vegetarian]), Recipe(nr=2, name="B", tags=[vegetarian])]
    )
    await db_session.commit()
    db_session.expunge_all()

    recipes = (await db_session.scalars(select(Recipe).order_by(Recipe.nr))).all()

    assert [[t.name for t in r.tags] for r in recipes] == [["Vegetarian"], ["Vegetarian"]]
    assert len((await db_session.scalars(select(Tag))).all()) == 1


async def test_same_tag_attached_twice_is_rejected(db_session):
    db_session.add(Recipe(nr=1, name="A", tags=[Tag(name="Quick")]))
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("INSERT INTO recipe_tags (recipe_id, tag_id) SELECT recipe_id, tag_id FROM recipe_tags")
        )


async def link_count(session, recipe_nr=None) -> int:
    query = "SELECT count(*) FROM recipe_tags"
    if recipe_nr is not None:
        query += " WHERE recipe_id = (SELECT id FROM recipes WHERE nr = :nr)"
    return await session.scalar(text(query), {"nr": recipe_nr})


async def test_deleting_recipe_removes_only_its_links(db_session):
    soup = Tag(name="Soup")
    doomed = Recipe(nr=1, name="Doomed", tags=[soup])
    survivor = Recipe(nr=2, name="Survivor", tags=[soup])
    db_session.add_all([doomed, survivor])
    await db_session.commit()

    await db_session.delete(doomed)
    await db_session.commit()
    db_session.expunge_all()

    assert await link_count(db_session) == 1
    assert (await db_session.scalars(select(Tag.name))).all() == ["Soup"]
    remaining = await db_session.scalar(select(Recipe))
    assert [t.name for t in remaining.tags] == ["Soup"]


async def test_deleting_recipe_directly_in_database_removes_its_links(db_session):
    db_session.add(Recipe(nr=1, name="Doomed", tags=[Tag(name="Soup"), Tag(name="Quick")]))
    await db_session.commit()

    await db_session.execute(text("DELETE FROM recipes WHERE nr = 1"))

    assert await link_count(db_session) == 0
    assert len((await db_session.scalars(select(Tag))).all()) == 2


async def test_deleting_tag_removes_it_from_recipes(db_session):
    quick = Tag(name="Quick")
    db_session.add(Recipe(nr=1, name="Dish", tags=[Tag(name="Soup"), quick]))
    await db_session.commit()

    await db_session.delete(quick)
    await db_session.commit()
    db_session.expunge_all()

    recipe = await db_session.scalar(select(Recipe))
    assert [t.name for t in recipe.tags] == ["Soup"]
