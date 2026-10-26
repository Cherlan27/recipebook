# Deployment Specification

## Purpose

Describes how the application is packaged, configured and operated on hardware the owner controls, so that the recipe book can run in a home network without depending on any third-party cloud service.

## Requirements

### Requirement: User interface and API are served from a single origin
The application SHALL serve both the user interface and the API from one network port, so that browser clients reach both under the same origin and no cross-origin configuration is required for operation.

#### Scenario: Visitor opens the application
- **WHEN** a browser requests the root path of the deployed application
- **THEN** the application responds with the user interface

#### Scenario: User interface calls the API
- **WHEN** the loaded user interface requests an API endpoint
- **THEN** the request targets the same origin the interface was served from
- **AND** the response is returned without requiring a cross-origin permission

### Requirement: Application is reachable from other devices on the local network
The deployed application SHALL accept requests addressed to the host machine's network address, so that other devices in the same home network can use it.

#### Scenario: Another device in the home network opens the application
- **WHEN** a device in the same local network requests the application at the host machine's IP address and the published port
- **THEN** the application responds with the user interface

### Requirement: Database location is configurable per deployment
The application SHALL read the filesystem location of its database from configuration rather than deriving it only from the source layout, so that a deployment can place the database on storage that outlives the running instance.

#### Scenario: Deployment supplies a database location
- **WHEN** the application starts with `RECIPEBOOK_DATABASE_PATH` set to a filesystem path
- **THEN** the application reads and writes its database at that path

#### Scenario: No database location is supplied
- **WHEN** the application starts without `RECIPEBOOK_DATABASE_PATH` set
- **THEN** the application uses its default location inside the backend project directory

### Requirement: Application data survives restarts and redeployments
Data written by the application SHALL remain available after the application instance is restarted, and after it is rebuilt and started again from a new image, as long as the configured storage location is preserved.

#### Scenario: Instance is restarted
- **GIVEN** data has been written to the database
- **WHEN** the application instance is stopped and started again
- **THEN** the previously written data is still readable

#### Scenario: Instance is rebuilt from a new image
- **GIVEN** data has been written to the database
- **WHEN** a new application image is built and the instance is recreated from it against the same storage location
- **THEN** the previously written data is still readable

### Requirement: Unusable storage is reported as a diagnosable startup failure
When the configured database location cannot be created or written to, the application SHALL fail to start with an error that names the offending path, instead of failing during module import with an unrelated error.

#### Scenario: Configured data directory is not writable
- **WHEN** the application starts with `RECIPEBOOK_DATABASE_PATH` pointing into a directory it cannot create or write
- **THEN** startup fails with an error message that identifies the configured path
- **AND** the process exits with a non-zero status

### Requirement: Deployed instance reports its own health
The deployment SHALL expose the running instance's health to its supervisor, so that a broken instance is visible without a manual request.

#### Scenario: Instance is serving requests
- **WHEN** the supervisor checks the health of a running instance that answers `GET /health` with `200 OK`
- **THEN** the instance is reported as healthy

#### Scenario: Instance stops answering
- **WHEN** the supervisor checks the health of an instance that no longer answers `GET /health` successfully
- **THEN** the instance is reported as unhealthy

### Requirement: The same deployment artifact builds for the development machine and the target device
The deployment SHALL be buildable without source changes for both the `linux/amd64` architecture of the development machine and the `linux/arm64` architecture of the Raspberry Pi, so that a deployment can be verified locally before it is applied to the target device.

#### Scenario: Built on the development machine
- **WHEN** the deployment artifact is built on a `linux/amd64` host
- **THEN** the build succeeds and the resulting instance serves the user interface and answers `GET /health` with `200 OK`

#### Scenario: Built on the target device
- **WHEN** the same deployment artifact is built unchanged on a `linux/arm64` host
- **THEN** the build succeeds and the resulting instance serves the user interface and answers `GET /health` with `200 OK`
