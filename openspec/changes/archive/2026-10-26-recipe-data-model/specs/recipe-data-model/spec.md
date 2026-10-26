## Purpose

Defines how recipes, their tags, and the links between them are persisted, and which integrity rules the stored data must always satisfy, so that all recipe features share one data basis compatible with the existing paper recipe system.

## ADDED Requirements

### Requirement: Recipes are stored with the fields of the paper system
The system SHALL persist recipes with the following fields: `nr` (integer), `name` (text), `effort` (integer), `time_minutes` (integer), `servings` (integer), `kid_friendly` (one of `yes`, `with_adjustments`, `no`), `ingredients` (free text, one line per ingredient), `steps` (free text, one line per step), `created_at` and `updated_at` (timestamps). Only `nr` and `name` SHALL be required; every other field SHALL be allowed to be empty, so that incomplete paper recipes can be captured.

#### Scenario: Several recipes with tags are stored and read back
- **WHEN** at least three recipes are stored, each with all fields filled and one or more tags
- **THEN** reading them back returns every recipe with the same field values and the same set of tags
- **AND** multi-line `ingredients` and `steps` keep their line breaks

#### Scenario: Recipe with only the required fields
- **WHEN** a recipe is stored with only `nr` and `name`
- **THEN** it is accepted
- **AND** every other field except the timestamps reads back as empty

#### Scenario: Recipe without a number
- **WHEN** a recipe without `nr` is stored
- **THEN** the database rejects it

#### Scenario: Recipe without a name
- **WHEN** a recipe without `name` is stored
- **THEN** the database rejects it

### Requirement: Recipe numbers are unique
The database SHALL reject a recipe whose `nr` is already used by another recipe, independent of any application-level check.

#### Scenario: Duplicate recipe number
- **GIVEN** a stored recipe with `nr` 12
- **WHEN** another recipe with `nr` 12 is written to the database
- **THEN** the database rejects it
- **AND** the existing recipe is unchanged

### Requirement: Effort is limited to 1 to 3
The database SHALL reject an `effort` value outside the range 1 to 3, even when the value is written directly to the database, bypassing the application's data model. An empty `effort` SHALL be allowed.

#### Scenario: Effort within range
- **WHEN** recipes with `effort` 1, 2, and 3 are stored
- **THEN** all of them are accepted

#### Scenario: Effort out of range
- **WHEN** a recipe with `effort` 0 or 4 is written directly to the database
- **THEN** the database rejects it

### Requirement: Kid-friendliness is limited to the defined values
The database SHALL reject a `kid_friendly` value other than `yes`, `with_adjustments`, or `no`, even when the value is written directly to the database. An empty `kid_friendly` SHALL be allowed.

#### Scenario: Defined value
- **WHEN** recipes with `kid_friendly` `yes`, `with_adjustments`, and `no` are stored
- **THEN** all of them are accepted and read back with the same value

#### Scenario: Undefined value
- **WHEN** a recipe with `kid_friendly` `maybe` is written directly to the database
- **THEN** the database rejects it

### Requirement: Timestamps are maintained automatically
The system SHALL set `created_at` and `updated_at` when a recipe is created, and SHALL update `updated_at` whenever a stored recipe is changed through the application, without the caller supplying either value. `created_at` SHALL NOT change after creation. Timestamps SHALL be recorded in UTC.

#### Scenario: Recipe is created
- **WHEN** a recipe is stored without timestamps
- **THEN** `created_at` and `updated_at` are both set to the time of creation

#### Scenario: Recipe is changed
- **GIVEN** a stored recipe
- **WHEN** one of its fields is changed and saved
- **THEN** `updated_at` is later than before the change
- **AND** `created_at` is unchanged

### Requirement: Tags are free-form, trimmed, and unique regardless of case
The system SHALL let tags be created with any non-empty name; there is no fixed list. Leading and trailing whitespace SHALL be removed before a tag is stored. Tag names SHALL be unique regardless of letter case, including non-ASCII letters such as German umlauts, and regardless of Unicode composition form (a letter written as one code point or as base letter plus combining mark is the same letter). Case folding treats `ß` and `ss` as equal. The stored spelling SHALL be the one used when the tag was first created.

#### Scenario: Tag name with surrounding whitespace
- **WHEN** a tag named `"  Pasta  "` is created
- **THEN** it is stored with the name `"Pasta"`

#### Scenario: Same name in different case
- **GIVEN** a stored tag `"Pasta"`
- **WHEN** a tag named `"pasta"` or `" PASTA "` is created
- **THEN** it is rejected as a duplicate
- **AND** the stored tag keeps the name `"Pasta"`

#### Scenario: Same name in different case with umlauts
- **GIVEN** a stored tag `"Österreichisch"`
- **WHEN** a tag named `"österreichisch"` is created
- **THEN** it is rejected as a duplicate

#### Scenario: Same name in a different Unicode form
- **GIVEN** a stored tag `"Österreichisch"` written with the precomposed letter `Ö`
- **WHEN** a tag is created with the same text written as `O` followed by a combining diaeresis
- **THEN** it is rejected as a duplicate

#### Scenario: Sharp s and double s
- **GIVEN** a stored tag `"Maße"`
- **WHEN** a tag named `"Masse"` is created
- **THEN** it is rejected as a duplicate

#### Scenario: Empty tag name
- **WHEN** a tag is created whose name is empty or consists only of whitespace
- **THEN** it is rejected

### Requirement: Recipes and tags are linked many-to-many
A recipe SHALL be able to carry any number of tags, and a tag SHALL be able to be attached to any number of recipes. The same tag SHALL be attached to a given recipe at most once.

#### Scenario: One tag on several recipes
- **WHEN** the tag `"Vegetarian"` is attached to two different recipes
- **THEN** both recipes list `"Vegetarian"` among their tags
- **AND** only one tag `"Vegetarian"` exists

#### Scenario: Same tag attached twice to one recipe
- **GIVEN** a recipe that carries the tag `"Quick"`
- **WHEN** a second link between that recipe and `"Quick"` is written to the database
- **THEN** the database rejects it

### Requirement: Deleting a recipe or a tag removes only its links
Deleting a recipe SHALL remove the links between that recipe and its tags, and the tags themselves SHALL remain. Deleting a tag SHALL remove it from every recipe it was attached to, and the recipes themselves SHALL remain. The database SHALL enforce this, so that no link refers to a recipe or tag that no longer exists.

#### Scenario: Recipe is deleted
- **GIVEN** two recipes that both carry the tag `"Soup"`
- **WHEN** one of the recipes is deleted
- **THEN** no link to the deleted recipe remains
- **AND** the tag `"Soup"` still exists
- **AND** the other recipe still carries the tag `"Soup"`

#### Scenario: Recipe is deleted directly in the database
- **GIVEN** a recipe that carries tags
- **WHEN** the recipe row is deleted with a direct database statement, bypassing the application's data model
- **THEN** no link to the deleted recipe remains
- **AND** the tags still exist

#### Scenario: Tag is deleted
- **GIVEN** a recipe that carries the tags `"Soup"` and `"Quick"`
- **WHEN** the tag `"Quick"` is deleted
- **THEN** the recipe still exists and carries only the tag `"Soup"`
