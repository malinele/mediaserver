# Operations Runbook

## Bootstrapping

1. Deploy the stack with `docker compose up -d` from the repository root.
2. Seed configuration with `./tools/mctl.py import-config ./config`.
3. Verify the controller is healthy at `http://localhost:8080/v1/health`.

## Provisioning Nimble nodes

1. Ensure the Nimble API keys (`NIMBLE_A_KEY`, `NIMBLE_B_KEY`) are stored in Vault and injected as environment variables.
2. Trigger reconciliation for each stream:
   ```bash
   ./tools/mctl.py reconcile TT-2025-10-07-001
   ```
3. Watch the controller logs for adapter errors.

## Generating playback URLs

Use the CLI to sign a URL:
```bash
./tools/mctl.py sign --client betsson --stream TT-2025-10-07-001 --primary
```
Repeat with `--backup` during failover drills.

## Observability

- Prometheus endpoint is exposed at `http://localhost:8080/metrics` (to be implemented).
- Grafana dashboards are shipped in `deploy/grafana`.
- Alert on `media_ingest_up == 0` and part age > 1.5s.

## Incident Response

1. Run `./tools/mctl.py reconcile <stream>` to re-apply configuration.
2. Rotate signing keys if compromised via `POST /v1/keys/rotate`.
3. Engage streaming vendors if adapter calls fail repeatedly.
