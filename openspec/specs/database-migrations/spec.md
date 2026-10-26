# Database Migrations Specification

## Purpose

Keeps the database schema versioned and brings an existing database up to the version the application expects at startup, without losing stored data and with a copy of the database file to fall back on.

## Requirements

### Requirement: Schema is brought up to date at application start
On every start, before it serves any request, the application SHALL apply all schema migrations that the configured database has not yet received, in order. This SHALL happen the same way for local development and for the container deployment, without a separate command or entrypoint step.

#### Scenario: Application starts without a database file
- **GIVEN** no file exists at the configured database location
- **WHEN** the application starts
- **THEN** the database file is created with the complete current schema
- **AND** the database records the latest schema version as its current version

#### Scenario: Application starts against an up-to-date database
- **GIVEN** a database that already has every migration applied
- **WHEN** the application starts again
- **THEN** no migration is applied
- **AND** the schema and the recorded schema version are unchanged

#### Scenario: Application starts against a database with pending migrations and existing data
- **GIVEN** a database file that contains data and is behind the latest schema version
- **WHEN** the application starts
- **THEN** the database records the latest schema version as its current version
- **AND** every row that existed before the start is still present with unchanged content

#### Scenario: Restart of an up-to-date database with stored recipes
- **GIVEN** a database at the latest schema version that contains recipes with tags
- **WHEN** the application starts again
- **THEN** all recipes, tags, and their links are still present with unchanged content

### Requirement: Migrations define the complete schema
The versioned migrations SHALL produce exactly the schema the application's data model expects, so that a database built only from migrations works with the application without any implicit table creation.

#### Scenario: Migrated database matches the application's data model
- **GIVEN** an empty database
- **WHEN** all migrations are applied
- **THEN** comparing the resulting schema against the application's data model definition reports no differences

### Requirement: Database file is copied before pending migrations run
When the configured database file already exists and has pending migrations, the application SHALL copy the file before applying any migration. The copy SHALL be placed in the same directory as the database file and be named after it with the suffix `.bak-<revision>`, where `<revision>` is the schema version the database had before the migration, or `base` if it had none (e.g. `app.db.bak-base`). An existing copy with that name SHALL NOT be overwritten, and the application SHALL log a warning naming it. A copy that could not be written completely SHALL NOT remain under that name. The application SHALL log the revision change and every copy it writes.

#### Scenario: Existing database with pending migrations
- **GIVEN** an existing database file at schema version `<revision>` with pending migrations
- **WHEN** the application starts
- **THEN** a file `<database file name>.bak-<revision>` exists next to the database file
- **AND** its content is identical to the database file as it was before the start

#### Scenario: Existing database without a recorded schema version
- **GIVEN** an existing database file that has never been migrated
- **WHEN** the application starts
- **THEN** a file `<database file name>.bak-base` exists next to the database file

#### Scenario: Nothing is pending
- **GIVEN** an existing database file that already has every migration applied
- **WHEN** the application starts
- **THEN** no new backup copy is created

#### Scenario: Database is created on this start
- **GIVEN** no file exists at the configured database location
- **WHEN** the application starts
- **THEN** no backup copy is created

#### Scenario: A backup copy with the same name already exists
- **GIVEN** an existing database file at schema version `<revision>` with pending migrations
- **AND** a file `<database file name>.bak-<revision>` already exists next to it
- **WHEN** the application starts
- **THEN** the existing backup copy keeps its previous content

#### Scenario: Backup copy is interrupted
- **GIVEN** an existing database file with pending migrations
- **AND** writing the backup copy fails after part of the file was written
- **WHEN** the application starts, fails, and starts again
- **THEN** the second start writes a complete copy that is identical to the database file as it was before the first start

#### Scenario: Backup copy cannot be written
- **GIVEN** an existing database file with pending migrations
- **AND** the backup copy cannot be written
- **WHEN** the application starts
- **THEN** startup fails with an error that names the backup path
- **AND** no migration is applied

### Requirement: A failing migration prevents startup
If applying a migration fails, the application SHALL NOT start serving requests. Startup SHALL fail with an error that states that a database migration failed and includes the underlying cause, and the process SHALL exit with a non-zero status.

#### Scenario: Migration raises an error
- **GIVEN** a pending migration that fails when applied
- **WHEN** the application starts
- **THEN** startup fails before any request is served
- **AND** the error message states that a database migration failed
- **AND** the error message contains the underlying cause reported by the failing migration

### Requirement: A database with dangling foreign keys prevents startup
On every start, after pending migrations have been applied (or found absent), the application SHALL verify that no row in the database refers to a row that does not exist, and if one does, it SHALL NOT start serving requests. Startup SHALL fail with an error that states that the database has foreign key violations, names the offending tables and rows, and names the next step (restore a backup copy or repair the rows); the process SHALL exit with a non-zero status. The error SHALL NOT attribute the violations to the migration, because they may have been caused by an edit outside the application. The check SHALL run on every start, so that an automatic restart cannot bring up an instance whose previous start was refused.

#### Scenario: A migration leaves a dangling row
- **GIVEN** a pending migration that completes but leaves a row whose foreign key points at no existing row
- **WHEN** the application starts
- **THEN** startup fails before any request is served
- **AND** the error message states that the database has foreign key violations and names the offending table

#### Scenario: A dangling row is still present at the next start
- **GIVEN** a database at the latest schema version that contains a row whose foreign key points at no existing row
- **WHEN** the application starts again
- **THEN** no migration is applied
- **AND** startup fails again with the same kind of error

#### Scenario: A row was orphaned outside the application
- **GIVEN** a database at the latest schema version in which a parent row was deleted directly in the database with foreign key enforcement off, leaving a dangling link row
- **WHEN** the application starts
- **THEN** startup fails with an error that states that the database has foreign key violations
- **AND** the error message does not state that a database migration failed

### Requirement: Deployed instance migrates its database on container start
The container deployment SHALL apply pending migrations to the database in the mounted data directory when the container starts, and the backup copy SHALL be written to that same mounted directory.

#### Scenario: Container starts on the Raspberry Pi with the database from the previous release
- **GIVEN** the deployed instance on the Raspberry Pi has an existing database in its mounted data directory
- **WHEN** the new release is deployed with `docker compose up -d --build`
- **THEN** the container log shows no migration error, `GET /health` answers `200 OK`, and a `app.db.bak-<revision>` file is present in the mounted data directory on the host
- **AND** this is verified by a manual deployment check on the Raspberry Pi
