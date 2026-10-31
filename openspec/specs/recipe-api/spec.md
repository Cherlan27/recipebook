# Recipe API Specification

## Purpose

Read-only HTTP endpoints that return the stored recipes as JSON, so that the user interface can show an overview and a single recipe.

## Requirements

### Requirement: Recipe list endpoint returns all recipes sorted by number
`GET /api/recipes` SHALL return `200` with a JSON array of all stored recipes, sorted by `nr` in ascending order, without pagination. Each entry SHALL contain `id`, `nr`, `name`, `effort`, `time_minutes`, `kid_friendly`, and `tags`. `tags` SHALL be an array of tag names sorted by name. Empty fields SHALL be `null`.

#### Scenario: List is sorted by number
- **GIVEN** stored recipes with `nr` 12, 3, and 7, stored in that order
- **WHEN** a client requests `GET /api/recipes`
- **THEN** the response is `200`
- **AND** the array contains the three recipes in the order `nr` 3, 7, 12

#### Scenario: List entries carry the overview fields
- **GIVEN** a stored recipe with all fields filled and the tags `"Quick"` and `"Pasta"`
- **WHEN** a client requests `GET /api/recipes`
- **THEN** its entry contains `id`, `nr`, `name`, `effort`, `time_minutes`, `kid_friendly` with the stored values
- **AND** `tags` is `["Pasta", "Quick"]`

#### Scenario: List entry of a recipe with only the required fields
- **GIVEN** a stored recipe with only `nr` and `name`
- **WHEN** a client requests `GET /api/recipes`
- **THEN** its `effort`, `time_minutes`, and `kid_friendly` are `null`
- **AND** `tags` is an empty array

#### Scenario: Empty database
- **GIVEN** no stored recipes
- **WHEN** a client requests `GET /api/recipes`
- **THEN** the response is `200` with an empty array

### Requirement: Recipe detail endpoint returns one recipe with all fields
`GET /api/recipes/{id}` SHALL return `200` with the recipe whose `id` matches. The response SHALL contain `id`, `nr`, `name`, `effort`, `time_minutes`, `servings`, `kid_friendly`, `ingredients`, `steps`, `tags` (tag names sorted by name), `created_at`, and `updated_at`. `ingredients` and `steps` SHALL be returned as the stored free text with its line breaks. Empty fields SHALL be `null`.

#### Scenario: Detail with all fields
- **GIVEN** a stored recipe with all fields filled, multi-line `ingredients` and `steps`, and two tags
- **WHEN** a client requests `GET /api/recipes/{id}` with its `id`
- **THEN** the response is `200`
- **AND** every field has the stored value, `ingredients` and `steps` keep their line breaks
- **AND** `tags` contains both tag names

#### Scenario: Unknown id
- **GIVEN** no stored recipe with `id` 999
- **WHEN** a client requests `GET /api/recipes/999`
- **THEN** the response is `404`
