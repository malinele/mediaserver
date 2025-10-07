# REST API Overview

The FastAPI application exposes the following endpoints under `/v1`:

- `POST /clients` – create or update a client.
- `GET /clients/{id}` – fetch a client.
- `POST /playback-profiles` – register a playback profile.
- `POST /streams` – register a stream desired state.
- `POST /sign` – return a signed LL-HLS URL for a client/stream pair.
- `POST /reconcile/{stream_id}` – trigger reconciliation on both adapters.
- `GET /stats/streams/{stream_id}` – fetch aggregated stream stats.
- `POST /keys/rotate` – rotate signer secret.
- `GET /health` and `GET /ready` – health probes.
- `GET /admin` – simple HTML admin overview.

Refer to the generated OpenAPI schema from the running service at `/openapi.json` or `/docs`.
