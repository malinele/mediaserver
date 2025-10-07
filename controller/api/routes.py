"""REST API routes for the controller."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from ..core.models import Client, PlaybackProfile, SignRequest, SignResponse, Stream
from ..core.policy import AuthorizationError
from ..state import AppState

router = APIRouter(prefix="/v1")


def get_state() -> AppState:
    from ..app import state

    return state


@router.post("/clients", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(client: Client, app: AppState = Depends(get_state)) -> Client:
    app.repository.add_client(client)
    return client


@router.get("/clients", response_model=list[Client])
async def list_clients(app: AppState = Depends(get_state)) -> list[Client]:
    return list(app.repository.clients.values())


@router.get("/clients/{client_id}", response_model=Client)
async def read_client(client_id: str, app: AppState = Depends(get_state)) -> Client:
    client = app.repository.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    return client


@router.post("/playback-profiles", response_model=PlaybackProfile, status_code=status.HTTP_201_CREATED)
async def create_profile(profile: PlaybackProfile, app: AppState = Depends(get_state)) -> PlaybackProfile:
    app.repository.add_playback_profile(profile)
    return profile


@router.get("/playback-profiles", response_model=list[PlaybackProfile])
async def list_profiles(app: AppState = Depends(get_state)) -> list[PlaybackProfile]:
    return list(app.repository.playback_profiles.values())


@router.post("/streams", response_model=Stream, status_code=status.HTTP_201_CREATED)
async def create_stream(stream: Stream, app: AppState = Depends(get_state)) -> Stream:
    app.repository.add_stream(stream)
    return stream


@router.get("/streams", response_model=list[Stream])
async def list_streams(app: AppState = Depends(get_state)) -> list[Stream]:
    return list(app.repository.streams.values())


@router.post("/sign", response_model=SignResponse)
async def sign(request: SignRequest, app: AppState = Depends(get_state)) -> SignResponse:
    try:
        url, ttl, kid = await app.sign(request)
    except AuthorizationError as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.reason) from exc
    return SignResponse(url=url, ttl=ttl, kid=kid)


@router.post("/reconcile/{stream_id}")
async def reconcile(stream_id: str, app: AppState = Depends(get_state)) -> dict[str, str]:
    await app.reconcile(stream_id)
    return {"status": "ok"}


@router.get("/stats/streams/{stream_id}")
async def stream_stats(stream_id: str, app: AppState = Depends(get_state)):
    try:
        return await app.fetch_stats(stream_id)
    except ValueError as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/keys/rotate")
async def rotate_key(payload: dict[str, str], app: AppState = Depends(get_state)) -> dict[str, str]:
    kid = payload.get("kid")
    secret = payload.get("secret")
    if not kid or not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="kid and secret required")
    new_kid = await app.rotate_key(kid, secret)
    return {"kid": new_kid}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/admin", response_class=HTMLResponse)
async def admin_home(app: AppState = Depends(get_state)) -> str:
    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Media Controller Admin</title>
  <style>
    :root { color-scheme: light dark; font-family: 'Inter', 'Segoe UI', sans-serif; }
    body { margin: 0; background: #f6f8fa; color: #0f172a; }
    header { background: #0f172a; color: #f8fafc; padding: 1.5rem 2rem; }
    header h1 { margin: 0 0 0.5rem; font-size: 1.75rem; }
    header p { margin: 0; opacity: 0.75; }
    main { padding: 2rem; display: grid; gap: 1.5rem; }
    .card { background: #ffffff; border-radius: 12px; padding: 1.75rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
    h2 { margin-top: 0; font-size: 1.25rem; }
    form { display: grid; gap: 1rem; }
    label { display: grid; gap: 0.4rem; font-weight: 600; font-size: 0.95rem; }
    input[type="text"], input[type="number"], textarea, select { padding: 0.6rem 0.75rem; border: 1px solid #cbd5f5; border-radius: 8px; font-size: 0.95rem; }
    input[type="checkbox"] { transform: scale(1.1); }
    button { padding: 0.65rem 1rem; border-radius: 8px; background: #2563eb; border: 0; color: white; font-weight: 600; cursor: pointer; box-shadow: 0 5px 20px rgba(37, 99, 235, 0.35); }
    button[disabled] { cursor: not-allowed; opacity: 0.55; box-shadow: none; }
    .muted { font-size: 0.85rem; color: #475569; }
    .grid-2 { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 0.65rem 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
    th { background: #f1f5f9; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }
    tbody tr:hover { background: rgba(37, 99, 235, 0.06); }
    textarea { min-height: 90px; resize: vertical; }
    .tiles { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
    .tile { border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; background: #fff; position: relative; }
    .tile h3 { margin: 0 0 0.25rem; font-size: 1.05rem; }
    .status { font-weight: 600; margin-bottom: 0.5rem; }
    .status.ok { color: #15803d; }
    .status.unavailable, .status.unknown { color: #b91c1c; }
    .result, .meta { background: #0f172a; color: #e2e8f0; padding: 0.75rem; border-radius: 8px; white-space: pre-wrap; font-family: 'Fira Code', monospace; font-size: 0.85rem; }
    .meta { background: #1e293b; margin-top: 0.75rem; }
    @media (max-width: 768px) { main { padding: 1rem; } header { padding: 1rem; } }
  </style>
</head>
<body>
  <header>
    <h1>Media Controller Admin</h1>
    <p>Provision clients, sign LL-HLS URLs, and keep an eye on ingest health.</p>
  </header>
  <main>
    <section class=\"card\">
      <h2>Create Client</h2>
      <form id=\"client-form\">
        <div class=\"grid-2\">
          <label>Client ID<input id=\"client-id\" type=\"text\" required placeholder=\"betsson\" /></label>
          <label>Display Name<input id=\"client-display-name\" type=\"text\" required placeholder=\"Betsson\" /></label>
        </div>
        <label>Playback Profile<select id=\"client-profile\" required></select></label>
        <div class=\"grid-2\">
          <label>Token TTL (seconds)<input id=\"client-ttl\" type=\"number\" min=\"10\" value=\"90\" /></label>
          <label>Max Sessions<input id=\"client-max-sessions\" type=\"number\" min=\"1\" value=\"1\" /></label>
        </div>
        <label>IP Allowlist<input id=\"client-ip\" type=\"text\" placeholder=\"203.0.113.0/24, 198.51.100.0/24\" /></label>
        <div class=\"grid-2\">
          <label>Geo Allow Countries<input id=\"client-geo-allow\" type=\"text\" placeholder=\"SE,EE,LT\" /></label>
          <label>Geo Deny Countries<input id=\"client-geo-deny\" type=\"text\" placeholder=\"US,FR\" /></label>
        </div>
        <div class=\"grid-2\">
          <label class=\"muted\"><input id=\"client-watermark-enabled\" type=\"checkbox\" /> Enable Watermark</label>
          <label>Watermark Template<input id=\"client-watermark-template\" type=\"text\" placeholder=\"ACME | {match_id} | {utc_ts}\" /></label>
        </div>
        <button type=\"submit\">Create Client</button>
      </form>
      <div id=\"client-result\" class=\"meta\" style=\"display:none;\"></div>
    </section>

    <section class=\"card\">
      <h2>Copy Primary / Backup URLs</h2>
      <form id=\"sign-form\" class=\"grid-2\">
        <label>Client<select id=\"sign-client\" required></select></label>
        <label>Stream<select id=\"sign-stream\" required></select></label>
        <label class=\"muted\"><input id=\"sign-use-backup\" type=\"checkbox\" /> Use backup (Nimble B)</label>
        <button id=\"sign-button\" type=\"submit\">Generate URL</button>
      </form>
      <textarea id=\"sign-output\" readonly placeholder=\"Click Generate to fetch a signed LL-HLS URL\"></textarea>
      <div id=\"sign-meta\" class=\"meta\" style=\"display:none;\"></div>
      <button id=\"failover-button\" type=\"button\">Run Failover Test</button>
      <div id=\"failover-output\" class=\"result\" style=\"display:none;\"></div>
    </section>

    <section class=\"card\">
      <h2>Clients</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Profile</th><th>TTL</th><th>Max Sessions</th><th>Watermark</th></tr>
        </thead>
        <tbody id=\"clients-table\"><tr><td colspan=\"5\">Loading…</td></tr></tbody>
      </table>
    </section>

    <section class=\"card\">
      <h2>Stream Health</h2>
      <div id=\"stats-grid\" class=\"tiles\"></div>
      <p class=\"muted\">Stats poll every 15 seconds. Errors show when Nimble endpoints are unreachable.</p>
    </section>
  </main>

  <script>
    const state = { profiles: [], streams: [], clients: [] };

    function splitList(value) {
      return value.split(',').map(part => part.trim()).filter(Boolean);
    }

    function updateProfileOptions() {
      const select = document.getElementById('client-profile');
      select.innerHTML = '';
      for (const profile of state.profiles) {
        const option = document.createElement('option');
        option.value = profile.name;
        option.textContent = `${profile.name} (${profile.renditions.length} renditions)`;
        select.appendChild(option);
      }
    }

    function updateClientOptions() {
      const select = document.getElementById('sign-client');
      select.innerHTML = '';
      for (const client of state.clients) {
        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = `${client.display_name} (${client.id})`;
        select.appendChild(option);
      }
    }

    function updateStreamOptions() {
      const select = document.getElementById('sign-stream');
      select.innerHTML = '';
      for (const stream of state.streams) {
        const option = document.createElement('option');
        option.value = stream.id;
        option.textContent = `${stream.id} — ${stream.packaging.ll_hls_path}`;
        select.appendChild(option);
      }
    }

    function updateSignControls() {
      const hasClient = state.clients.length > 0;
      const hasStream = state.streams.length > 0;
      document.getElementById('sign-button').disabled = !(hasClient && hasStream);
      document.getElementById('failover-button').disabled = !(hasClient && hasStream);
    }

    function renderClientsTable() {
      const tbody = document.getElementById('clients-table');
      tbody.innerHTML = '';
      if (!state.clients.length) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 5;
        cell.textContent = 'No clients configured yet.';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
      }
      for (const client of state.clients) {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${client.id}</td><td>${client.playback_profile}</td><td>${client.token_ttl_seconds}s</td><td>${client.max_sessions}</td><td>${client.watermark?.enabled ? 'Enabled' : 'Disabled'}</td>`;
        tbody.appendChild(row);
      }
    }

    async function loadData() {
      const [profilesRes, streamsRes, clientsRes] = await Promise.all([
        fetch('/v1/playback-profiles'),
        fetch('/v1/streams'),
        fetch('/v1/clients')
      ]);
      state.profiles = profilesRes.ok ? await profilesRes.json() : [];
      state.streams = streamsRes.ok ? await streamsRes.json() : [];
      state.clients = clientsRes.ok ? await clientsRes.json() : [];
      updateProfileOptions();
      updateClientOptions();
      updateStreamOptions();
      updateSignControls();
      renderClientsTable();
      refreshStats();
    }

    document.getElementById('client-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = {
        id: document.getElementById('client-id').value.trim(),
        display_name: document.getElementById('client-display-name').value.trim(),
        playback_profile: document.getElementById('client-profile').value,
        token_ttl_seconds: Number(document.getElementById('client-ttl').value) || 60,
        ip_allowlist: splitList(document.getElementById('client-ip').value),
        geo: {
          allow_countries: splitList(document.getElementById('client-geo-allow').value),
          deny_countries: splitList(document.getElementById('client-geo-deny').value)
        },
        max_sessions: Number(document.getElementById('client-max-sessions').value) || 1,
        watermark: {
          enabled: document.getElementById('client-watermark-enabled').checked,
          template: document.getElementById('client-watermark-template').value.trim() || null
        }
      };

      const resultEl = document.getElementById('client-result');
      resultEl.style.display = 'none';

      const response = await fetch('/v1/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        resultEl.textContent = `Failed to create client: ${response.status}`;
        resultEl.style.display = 'block';
        return;
      }

      const created = await response.json();
      state.clients.push(created);
      document.getElementById('client-form').reset();
      renderClientsTable();
      updateClientOptions();
      updateSignControls();
      resultEl.textContent = `Client ${created.id} created with TTL ${created.token_ttl_seconds}s.`;
      resultEl.style.display = 'block';
    });

    async function requestSignature(useBackup) {
      const payload = {
        client_id: document.getElementById('sign-client').value,
        stream_id: document.getElementById('sign-stream').value,
        use_backup: Boolean(useBackup)
      };
      const response = await fetch('/v1/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        throw new Error(`Sign request failed: ${response.status}`);
      }
      return await response.json();
    }

    document.getElementById('sign-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      try {
        const data = await requestSignature(document.getElementById('sign-use-backup').checked);
        const output = document.getElementById('sign-output');
        output.value = data.url;
        const meta = document.getElementById('sign-meta');
        meta.textContent = `kid ${data.kid} • TTL ${data.ttl}s • Backup=${document.getElementById('sign-use-backup').checked}`;
        meta.style.display = 'block';
      } catch (err) {
        document.getElementById('sign-output').value = '';
        const meta = document.getElementById('sign-meta');
        meta.textContent = err.message;
        meta.style.display = 'block';
      }
    });

    document.getElementById('failover-button').addEventListener('click', async () => {
      const output = document.getElementById('failover-output');
      output.style.display = 'block';
      output.textContent = 'Running failover test…';
      try {
        const [primary, backup] = await Promise.all([
          requestSignature(false),
          requestSignature(true)
        ]);
        output.textContent = `Primary URL:\n${primary.url}\n\nBackup URL:\n${backup.url}`;
      } catch (err) {
        output.textContent = `Failover test failed: ${err.message}`;
      }
    });

    function formatMetric(value, suffix = '') {
      if (value === null || value === undefined) {
        return '—';
      }
      return `${value}${suffix}`;
    }

    async function refreshStats() {
      const container = document.getElementById('stats-grid');
      container.innerHTML = '';
      if (!state.streams.length) {
        const empty = document.createElement('p');
        empty.textContent = 'No streams configured yet.';
        container.appendChild(empty);
        return;
      }
      const cards = new Map();
      for (const stream of state.streams) {
        const card = document.createElement('div');
        card.className = 'tile';
        card.innerHTML = `<h3>${stream.id}</h3><p class=\"status unknown\">Loading…</p><p>Part age: —</p><p>Segment age: —</p><p>CPU: —</p><p>HTTP errors: —</p>`;
        cards.set(stream.id, card);
        container.appendChild(card);
      }
      const results = await Promise.all(state.streams.map(async (stream) => {
        try {
          const res = await fetch(`/v1/stats/streams/${encodeURIComponent(stream.id)}`);
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }
          return await res.json();
        } catch (err) {
          return { stream_id: stream.id, ingest_status: 'unavailable', error: err.message };
        }
      }));
      for (const stats of results) {
        const card = cards.get(stats.stream_id);
        if (!card) continue;
        const statusEl = card.querySelector('.status');
        const status = (stats.ingest_status || 'unknown').toLowerCase();
        statusEl.textContent = `Ingest: ${stats.ingest_status || 'unknown'}`;
        statusEl.className = `status ${status}`;
        const paragraphs = card.querySelectorAll('p');
        if (paragraphs.length >= 5) {
          paragraphs[1].textContent = `Part age: ${formatMetric(stats.last_part_age_seconds, 's')}`;
          paragraphs[2].textContent = `Segment age: ${formatMetric(stats.last_segment_age_seconds, 's')}`;
          paragraphs[3].textContent = `CPU: ${formatMetric(stats.cpu_percent, '%')}`;
          paragraphs[4].textContent = `HTTP errors: ${formatMetric(stats.http_error_rate, '%')}`;
        }
        if (stats.error) {
          const errorNote = document.createElement('p');
          errorNote.className = 'muted';
          errorNote.textContent = `Adapter error: ${stats.error}`;
          card.appendChild(errorNote);
        }
      }
    }

    setInterval(refreshStats, 15000);
    loadData();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)
