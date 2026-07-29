# Deployment Guide — Developer Brain

## What changed (read this first)

The previous version couldn't deploy to the cloud because of a few bugs:

1. **`backend/requirements.txt` didn't list Django at all** — it still had
   the old FastAPI dependencies. Any platform that runs `pip install -r
   requirements.txt` (Render, Railway, etc.) would fail immediately. Fixed:
   requirements.txt now lists Django, DRF, gunicorn, whitenoise, and the RAG
   stack.
2. **`DEBUG = True` and `ALLOWED_HOSTS = []` were hardcoded** — deploying
   with debug on is a security problem, and an empty `ALLOWED_HOSTS` makes
   Django reject every request once `DEBUG=False`. Fixed: both now come
   from environment variables.
3. **No static file serving in production.** Django doesn't serve static
   files itself once `DEBUG=False`, so the built React UI (`frontend/dist`)
   would load as a blank/unstyled page even if the server came up. Fixed:
   added [WhiteNoise](https://whitenoise.readthedocs.io/), which serves the
   built frontend directly from the Django process.
4. **`manage.py runserver` was the production command** — that's Django's
   single-threaded dev server, not meant for real traffic. Fixed: switched
   to `gunicorn`.
5. **Migrations/`collectstatic` ran at Docker *build* time**, before any
   real database or volume was attached. Fixed: moved to `entrypoint.sh`,
   which runs them at container *start*.

I verified the fix by actually running `migrate` and `collectstatic` with
`DEBUG=False` locally — both now complete cleanly and pick up the built
frontend assets.

---

## Option A — Docker (recommended, matches what's in this repo)

```bash
cp .env.docker.example .env   # add your OPENAI_API_KEY if you have one
docker-compose up --build
```

- App: `http://localhost:8000` (Django serves the built React UI directly —
  there's no separate frontend container needed for this to work)
- Neo4j browser: `http://localhost:7474` (user `neo4j`, password
  `devbrain123` — change this for anything beyond local use)

`entrypoint.sh` runs migrations and `collectstatic` automatically on every
container start, then launches gunicorn.

## Option B — Cloud PaaS without Docker (Render, Railway, etc.)

A `Procfile` is included at the repo root:

```
web: cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn devbrain_project.wsgi:application --bind 0.0.0.0:$PORT ...
```

Steps on Render (Railway is nearly identical):
1. New **Web Service** → connect this repo.
2. **Build command**: `pip install -r backend/requirements.txt`
3. **Start command**: leave blank if it picks up the `Procfile`, or paste
   the `web:` line above manually.
4. **Environment variables** (Settings → Environment):
   - `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = your Render URL, e.g. `devbrain.onrender.com`
     (Render also sets `RENDER_EXTERNAL_HOSTNAME` automatically, which
     `settings.py` now picks up as a fallback)
   - `DATABASE_URL` — attach Render's free Postgres add-on and paste its
     connection string here (see "Storage" note below for why this matters)
   - `OPENAI_API_KEY` — optional
   - `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` — only needed for the
     graph feature; you'll need a hosted Neo4j (e.g. Neo4j Aura free tier)
     since there's no Neo4j container on a plain PaaS deploy

---

## Option C — Google Cloud Run (free tier with enough memory for the embedding model)

A root-level `Dockerfile` (identical to `Dockerfile.backend`) is included so
Cloud Run's build auto-detects it, and `entrypoint.sh` already binds to
`$PORT`, which Cloud Run sets automatically (usually 8080) — no changes
needed there.

```bash
gcloud init                     # pick/create a project, enable billing (won't be charged within free tier)
gcloud run deploy devbrain \
  --source . \
  --memory 1Gi \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(50))"),DEBUG=False
```

Cloud Run gives you the service URL after deploy (something like
`devbrain-xxxx-uc.a.run.app`) — `ALLOWED_HOSTS` doesn't need to be set in
advance since `settings.py` falls back to allowing all hosts when the env
var is empty, but for a tighter setup, redeploy with
`--update-env-vars ALLOWED_HOSTS=devbrain-xxxx-uc.a.run.app` once you know it.

**Storage on Cloud Run is ephemeral** — the container's local disk resets
on every new revision/cold start, so SQLite and local Chroma data won't
persist. For a real deployment:
- Point `DATABASE_URL` at a free external Postgres — [Supabase](https://supabase.com)
  or [Neon](https://neon.tech) both have a free-forever tier.
- For Chroma, either accept re-ingesting after restarts (fine for
  occasional personal use), or mount a
  [Cloud Storage FUSE volume](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
  at `CHROMA_DIR`.

First request after idle time will be slow (~10-30s) while the embedding
model loads — that's normal for scale-to-zero.

## Option D — Render free tier + OpenAI embeddings (fits in 512MB)

Render's free tier (512MB) isn't enough for the local `sentence-transformers`
model. To fit, switch embeddings to OpenAI's API instead — this removes the
torch/model memory footprint entirely (the code already supports this, it's
just an env var switch):

Add these on top of the Option B env vars above:
| Key | Value |
|---|---|
| `EMBEDDING_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | your key |

This makes every ingest/query call OpenAI's embeddings endpoint instead of
running a local model — small per-call cost after your free trial credit
runs out, but no memory problem. `LLM_PROVIDER=openai` (already the config
default) will also then generate real answers instead of retrieval-only
mode, using the same key.

---

## Storage — please read before relying on this in production

- **SQLite and the local Chroma vector store both live on local disk.**
  Most free-tier PaaS containers (Render free, Railway without a volume)
  wipe local disk on every redeploy/restart. That means ingested chunks and
  any Django admin data can silently disappear.
  - For the database: set `DATABASE_URL` to a real Postgres instance
    (free tier is fine) instead of relying on the SQLite default.
  - For the vector store: attach a persistent disk/volume and point
    `CHROMA_DIR` at it, or plan to re-ingest after deploys.
- **The embedding model (`sentence-transformers`) needs real memory** —
  budget at least ~1GB RAM for the web service. On a 512MB free instance,
  the first ingest/embed request is a likely cause of an OOM crash. If you
  hit that, either upgrade the instance or set `WEB_CONCURRENCY=1` to
  reduce the number of gunicorn workers.

---

## Local development (no Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # DEBUG=True by default, fine for local use
python manage.py migrate
python manage.py runserver
```

Open `http://localhost:8000`. If you're editing the frontend, run
`npm run dev` inside `frontend/` separately and rebuild with `npm run
build` when you want Django to pick up the new UI (it serves whatever is
in `frontend/dist`).

---

## Ingesting content
Once deployed, use the **Ingest** tab:
- **Local Folder**: only works if the server process has access to that
  local path — i.e. local/Docker deployments, not most cloud PaaS.
- **Upload ZIP**: works everywhere, including cloud deployments — zip your
  project, upload it, and it's extracted and ingested server-side.

---

## Troubleshooting

**"DisallowedHost at /" error** → `ALLOWED_HOSTS` doesn't include the
domain you're hitting. Add it as an env var.

**UI loads but looks unstyled / 404s on `/static/...`** → run `python
manage.py collectstatic --noinput` (the entrypoint/Procfile already do
this automatically — this is only relevant if you're running something
custom).

**"Microsoft Visual C++ 14.0 or greater is required" (Windows, installing
chromadb)** → use Docker (Option A above) instead, or install the
Microsoft C++ Build Tools ("Desktop development with C++" workload).

**"cp : Cannot find path .env.example" (PowerShell)** → use `copy` instead
of `cp`.
