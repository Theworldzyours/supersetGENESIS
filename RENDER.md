# Deploying Superset on Render

This repository includes a production Dockerfile and `render.yaml` blueprint. **Render builds the Docker image on their infrastructure** - you don't need Docker locally.

## Quick Deploy Methods

### Method 1: Blueprint (Recommended)
Uses the `render.yaml` file to deploy everything at once:

```bash
# 1. Authenticate Render CLI (see below)
render login  # or set RENDER_API_KEY

# 2. Deploy from blueprint
render blueprint apply --file render.yaml
```

This creates:
- PostgreSQL database (`superset-db`)
- Web service with auto-generated `SUPERSET_SECRET_KEY`
- Health check at `/health`
- 1GB persistent disk

### Method 2: Manual Dashboard Setup
1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
3. Connect your repo
4. Select `render.yaml`
5. Render will automatically provision everything

### Method 3: Manual Web Service
1. **Create a PostgreSQL database** in Render Dashboard
2. **Create a Web Service**:
   - Environment: **Docker**
   - Repository: this repo
   - Dockerfile path: `Dockerfile`
   - Health check path: `/health`
3. Set environment variables:
   - `SUPERSET_SECRET_KEY`: generate with `openssl rand -base64 42`
   - `SUPERSET__SQLALCHEMY_DATABASE_URI`: your Postgres connection string

## Render CLI Authentication

Render CLI is used for **deployment management**, not building. Builds happen on Render's servers.

**Option A - Device code (interactive):**
```bash
render login
# Opens browser to authorize
```

**Option B - API key (for CI/CD):**
```bash
# Get API key from: https://dashboard.render.com/u/settings#api-keys
export RENDER_API_KEY=rnd_YOUR_KEY_HERE
render whoami  # verify
```

## Post-Deploy: Database Initialization

After Render builds and starts your service (or if it crash-loops due to missing tables):

1. Open **Shell** in the Render Dashboard (service page → Shell tab)
2. Run initialization commands:
   ```bash
   superset db upgrade
   superset init
   superset fab create-admin
   ```
3. Restart the service

Alternatively, use Render CLI:
```bash
# Get service ID
render services

# Open shell
render ssh <SERVICE_ID>

# Then run the commands above
```

## Useful Render CLI Commands

```bash
# Check deployment status
render services
render deploys list <SERVICE_ID>

# View logs
render logs <SERVICE_ID>

# Trigger manual deploy
render deploys create <SERVICE_ID>

# Open shell session
render ssh <SERVICE_ID>
```

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
