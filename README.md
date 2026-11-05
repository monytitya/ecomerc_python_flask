# Ecomerc API

## Run with PostgreSQL in Docker

Requirements: Docker Desktop with Docker Compose enabled.

The project already has a local `.env` for application settings. The Docker
database settings are in the separate, Git-ignored `.env.docker` file so the
existing Bakong credentials are preserved. For local development, start the
API and PostgreSQL from the project directory:

```bash
docker compose --env-file .env.docker up --build
```

Open the API at <http://localhost:8000> and interactive API documentation at
<http://localhost:8000/docs>. The API container waits for PostgreSQL to pass its
health check before starting. Tables are created by the application on startup.
Uploaded files and database data are kept in Docker volumes.

Open pgAdmin at <http://localhost:5050> and sign in with
`PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` from `.env.docker`.
In pgAdmin, choose **Add New Server** and set:

- **General → Name:** `Ecomerc`
- **Connection → Host name/address:** `db`
- **Connection → Port:** `5432`
- **Connection → Maintenance database:** the `POSTGRES_DB` value from `.env.docker`
- **Connection → Username / Password:** the `POSTGRES_USER` and `POSTGRES_PASSWORD` values from `.env.docker`

Use `db` as the hostname from pgAdmin; `localhost` would point to the pgAdmin
container itself. Port 5432 is for database clients, not a web page.

The `.env.docker` file has development-only database and pgAdmin credentials.
For anything beyond local development, replace both passwords with strong
secrets made of URL-safe characters (letters, numbers, `_`, `.`, `~`, or `-`).
Do not commit `.env.docker` or use the development passwords on a public server.

To stop the containers while keeping database and upload data:

```bash
docker compose --env-file .env.docker down
```

To also permanently remove the database and upload volumes:

```bash
docker compose --env-file .env.docker down --volumes
```

The final command deletes persisted local data.
