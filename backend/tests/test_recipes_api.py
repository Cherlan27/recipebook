import pytest

from app.models import KidFriendly, Recipe, Tag

pytestmark = pytest.mark.anyio


async def test_list_of_empty_database_is_an_empty_array(client):
    response = client.get("/api/recipes")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_is_sorted_by_number(client, db_session):
    db_session.add_all(
        [Recipe(nr=12, name="Twelve"), Recipe(nr=3, name="Three"), Recipe(nr=7, name="Seven")]
    )
    await db_session.commit()

    response = client.get("/api/recipes")

    assert response.status_code == 200
    assert [entry["nr"] for entry in response.json()] == [3, 7, 12]


async def test_list_entries_carry_the_overview_fields(client, db_session):
    db_session.add(
        Recipe(
            nr=5,
            name="Pasta",
            effort=2,
            time_minutes=25,
            servings=4,
            kid_friendly=KidFriendly.WITH_ADJUSTMENTS,
            ingredients="200 g Pasta",
            steps="Boil",
            tags=[Tag(name="Quick"), Tag(name="Pasta")],
        )
    )
    await db_session.commit()

    [entry] = client.get("/api/recipes").json()

    assert entry == {
        "id": entry["id"],
        "nr": 5,
        "name": "Pasta",
        "effort": 2,
        "time_minutes": 25,
        "kid_friendly": "with_adjustments",
        "tags": ["Pasta", "Quick"],
    }


async def test_list_entry_of_recipe_with_only_required_fields(client, db_session):
    db_session.add(Recipe(nr=1, name="Bread"))
    await db_session.commit()

    [entry] = client.get("/api/recipes").json()

    assert entry["effort"] is None
    assert entry["time_minutes"] is None
    assert entry["kid_friendly"] is None
    assert entry["tags"] == []
