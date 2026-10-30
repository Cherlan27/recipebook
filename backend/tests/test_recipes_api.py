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


async def test_detail_with_all_fields(client, db_session):
    recipe = Recipe(
        nr=5,
        name="Pasta",
        effort=2,
        time_minutes=25,
        servings=4,
        kid_friendly=KidFriendly.YES,
        ingredients="200 g Pasta\n1 Onion",
        steps="Boil water\nCook pasta",
        tags=[Tag(name="Quick"), Tag(name="Pasta")],
    )
    db_session.add(recipe)
    await db_session.commit()

    response = client.get(f"/api/recipes/{recipe.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == recipe.id
    assert body["nr"] == 5
    assert body["name"] == "Pasta"
    assert body["effort"] == 2
    assert body["time_minutes"] == 25
    assert body["servings"] == 4
    assert body["kid_friendly"] == "yes"
    assert body["ingredients"] == "200 g Pasta\n1 Onion"
    assert body["steps"] == "Boil water\nCook pasta"
    assert body["tags"] == ["Pasta", "Quick"]
    assert body["created_at"] == recipe.created_at.isoformat()
    assert body["updated_at"] == recipe.updated_at.isoformat()


async def test_detail_of_unknown_id_is_404(client):
    response = client.get("/api/recipes/999")

    assert response.status_code == 404
