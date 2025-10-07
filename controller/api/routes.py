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


@router.post("/streams", response_model=Stream, status_code=status.HTTP_201_CREATED)
async def create_stream(stream: Stream, app: AppState = Depends(get_state)) -> Stream:
    app.repository.add_stream(stream)
    return stream


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
    clients = app.repository.clients.values()
    streams = app.repository.streams.values()
    html = [
        "<html><head><title>Controller Admin</title></head><body>",
        "<h1>Controller Admin</h1>",
        "<section><h2>Clients</h2><ul>",
    ]
    for client in clients:
        html.append(f"<li><strong>{client.display_name}</strong> ({client.id}) – profile {client.playback_profile}</li>")
    html.append("</ul></section>")
    html.append("<section><h2>Streams</h2><ul>")
    for stream in streams:
        html.append(
            f"<li>{stream.id} – {stream.packaging.ll_hls_path}<br/>"
            f"Primary: {stream.adapters.primary.base_url}<br/>"
            f"Backup: {stream.adapters.backup.base_url}</li>"
        )
    html.append("</ul></section>")
    html.append("<p>Use the CLI to create new clients and rotate keys.</p>")
    html.append("</body></html>")
    return "".join(html)
