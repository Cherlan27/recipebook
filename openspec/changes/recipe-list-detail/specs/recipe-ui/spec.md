## Purpose

Lets the user browse all recipes in an overview and open a single recipe in a detail view, with clear hints when there is nothing to show or the backend cannot be reached.

## ADDED Requirements

### Requirement: Overview lists all recipes in API order
The overview SHALL be the start page of the user interface. It SHALL show every recipe returned by the recipe list endpoint, in the returned order (sorted by `nr`), with its `nr`, `name`, `effort`, `time_minutes`, `kid_friendly`, and tags. Empty fields SHALL be hidden.

#### Scenario: Overview shows recipes sorted by number
- **GIVEN** the list endpoint returns recipes with `nr` 3, 7, and 12
- **WHEN** the overview is opened
- **THEN** it shows the three recipes in the order 3, 7, 12, each with its `nr` and `name`
- **AND** it shows the effort, time, kid-friendliness, and tags of each recipe that has them

### Requirement: A click on a recipe opens its detail view
Each recipe in the overview SHALL link to its detail view. The address of the detail view SHALL contain the recipe `id`, not its `nr`, so that it survives a later change of `nr`. Opening that address directly SHALL show the same detail view.

#### Scenario: Recipe is opened from the overview
- **GIVEN** the overview shows a recipe with `id` 5 and `nr` 12
- **WHEN** the user clicks the recipe
- **THEN** the detail view of the recipe with `id` 5 is shown
- **AND** the address contains `5` as the recipe identifier

### Requirement: Detail view shows all filled fields
The detail view SHALL show `nr`, `name`, `effort`, `time_minutes`, `servings`, `kid_friendly`, tags, ingredients, and steps of the recipe. Fields without a value SHALL be hidden, including their label.

#### Scenario: Detail with all fields
- **GIVEN** the detail endpoint returns a recipe with all fields filled
- **WHEN** its detail view is opened
- **THEN** it shows the `nr`, `name`, effort, time, servings, kid-friendliness, tags, ingredients, and steps

#### Scenario: Detail with only the required fields
- **GIVEN** the detail endpoint returns a recipe with only `nr` and `name`
- **WHEN** its detail view is opened
- **THEN** it shows the `nr` and `name`
- **AND** it shows no label for effort, time, servings, kid-friendliness, tags, ingredients, or steps

#### Scenario: Unknown recipe
- **GIVEN** the detail endpoint answers `404`
- **WHEN** the detail view is opened
- **THEN** it shows a hint that the recipe does not exist and a link back to the overview

### Requirement: Ingredients and steps are shown line by line
The detail view SHALL show the ingredients as a bulleted list and the steps as a numbered list, with one entry per line of the stored free text. Lines that are empty or contain only whitespace SHALL NOT produce an entry. Both `\n` and `\r\n` SHALL count as line breaks.

#### Scenario: Line-wise ingredients and steps
- **GIVEN** a recipe with `ingredients` `"200 g Pasta\n\n1 Onion\n"` and `steps` `"Boil water\r\n  \r\nCook pasta"`
- **WHEN** its detail view is opened
- **THEN** the ingredients are a bulleted list with the entries `200 g Pasta` and `1 Onion`
- **AND** the steps are a numbered list with the entries `Boil water` and `Cook pasta`

### Requirement: Empty database shows a hint
When the list endpoint returns no recipes, the overview SHALL show a hint that no recipes exist yet, instead of an empty page.

#### Scenario: Empty-database hint
- **GIVEN** the list endpoint returns an empty array
- **WHEN** the overview is opened
- **THEN** it shows a hint that there are no recipes yet
- **AND** it shows no recipe entries

#### Scenario: Empty state on the Raspberry Pi
- **GIVEN** the application is deployed on the Raspberry Pi with an empty database
- **WHEN** the overview is opened from another device in the home network
- **THEN** it shows the empty-database hint
- **AND** this is verified manually as part of the deployment check

### Requirement: Unreachable backend shows a hint
When a request to the backend fails because of a network error or a server error (status `5xx`), the overview and the detail view SHALL show a short hint that the backend is not reachable, instead of an empty page or the empty-database hint.

#### Scenario: Backend-unreachable hint on the overview
- **GIVEN** the request to the list endpoint fails with a network error
- **WHEN** the overview is opened
- **THEN** it shows a hint that the backend is not reachable
- **AND** it does not show the empty-database hint

#### Scenario: Backend-unreachable hint on the detail view
- **GIVEN** the request to the detail endpoint answers with status `500`
- **WHEN** the detail view is opened
- **THEN** it shows a hint that the backend is not reachable
