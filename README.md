# Media Controller Monorepo

This repository contains a prototype media distribution controller that orchestrates Nimble Streamer nodes, signs LL-HLS URLs, and exposes a REST API with a minimal admin UI.

## Layout

```
/controller      # FastAPI service implementation
/config          # Seed configuration for clients, profiles, streams
/deploy          # Container images, docker-compose stack, observability bits
/docs            # Runbooks, OpenAPI summary, operator guides
/tools           # CLI utilities (mctl)
/tests           # Unit tests
```

## Quickstart

```bash
pip install poetry
poetry install
uvicorn controller.app:app --reload
```

The API will be available at `http://localhost:8000` (or `8080` if you run via Docker Compose). Explore `/docs` for Swagger UI.
