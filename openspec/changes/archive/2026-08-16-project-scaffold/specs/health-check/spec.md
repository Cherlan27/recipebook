## Purpose

Lets the frontend (and any other client) verify that the backend process is running and reachable before relying on it for other requests.

## ADDED Requirements

### Requirement: Health endpoint returns 200 OK
The backend SHALL expose a `GET /health` endpoint that responds with HTTP status `200 OK` when the backend process is running.

#### Scenario: Client checks backend health
- **WHEN** a client sends `GET /health` to the backend
- **THEN** the backend responds with HTTP status `200 OK`

### Requirement: Frontend dev origin is allowed via CORS
The backend SHALL allow cross-origin requests from the frontend development origin (`http://localhost:5173`), so the frontend can call backend endpoints directly without a proxy.

#### Scenario: Frontend calls the backend from the dev origin
- **WHEN** a browser page served from `http://localhost:5173` sends a request to a backend endpoint
- **THEN** the backend's response includes CORS headers that permit `http://localhost:5173` as the requesting origin
