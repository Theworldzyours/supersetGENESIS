# Deploying Superset on Render (Docker)

This repository includes a production Dockerfile at `./Dockerfile`. Render can build and run it directly.

## Quick setup

1. **Create a Postgres database** in Render (metadata DB).
2. **Create a Web Service** in Render:
   - Environment: **Docker**
   - Repository: this repo
   - Dockerfile path: `Dockerfile`
   - Health check path (recommended): `/health`
3. Set these Render environment variables on the Web Service:
   - `SUPERSET_SECRET_KEY`: strong random value (required)
   - `SUPERSET__SQLALCHEMY_DATABASE_URI`: your Render Postgres connection URI (required)

If you don’t set `SUPERSET__SQLALCHEMY_DATABASE_URI`, Superset will fall back to a local SQLite DB inside the container, which is not recommended for production.

## One-time initialization (use Render Shell / “Debug” console)

The Docker image starts Gunicorn but does **not** automatically migrate/init the metadata DB. After the service builds and starts (or if it crash-loops due to missing tables), open the service’s Shell/Console and run:

- `superset db upgrade`
- `superset init`
- `superset fab create-admin`

Then redeploy/restart the service.

## Debugging checklist (Render build + runtime logs)

### Build failures (Deploys → build log)

- If the build fails during the frontend step, look for `npm`/webpack output in the logs.
- If the build fails during Python dependency install, look for the first `uv`/`pip` error and confirm required system libs are present (they’re installed via `docker/apt-install.sh` in the Dockerfile).

### Runtime failures (Logs tab)

Common signals:

- **DB connection errors**: confirm `SUPERSET__SQLALCHEMY_DATABASE_URI` is set and points to the correct Render Postgres instance.
- **Secret key warning / session issues**: ensure `SUPERSET_SECRET_KEY` is set and stable (don’t rotate it casually).
- **Missing tables / migration errors**: rerun `superset db upgrade` in the Shell.

### Verifying the service

- Check `https://<your-service>.onrender.com/health` returns OK.
- If `/health` is OK but the UI errors, check the Logs tab for stack traces and validate your metadata DB and secret key settings.
