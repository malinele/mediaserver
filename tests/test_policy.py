import pytest

from controller.core.models import Client, GeoPolicy, SignRequest, Stream, StreamAdapters, PackagingSpec, IngestSpec, IngestSRT, AdapterSpec
from controller.core.policy import AuthorizationError, PolicyEngine


@pytest.fixture
def client() -> Client:
    return Client(
        id="betsson",
        display_name="Betsson",
        playback_profile="default_abr",
        token_ttl_seconds=60,
        ip_allowlist=["203.0.113.0/24"],
        geo=GeoPolicy(allow_countries=["SE", "EE"]),
        max_sessions=100,
        watermark={"enabled": True, "template": "X"},
    )


@pytest.fixture
def stream(client: Client) -> Stream:
    adapters = StreamAdapters(
        primary=AdapterSpec(kind="nimble", base_url="https://primary", api_key="k"),
        backup=AdapterSpec(kind="nimble", base_url="https://backup", api_key="k"),
    )
    return Stream(
        id="match-1",
        description="",
        adapters=adapters,
        ingest=IngestSpec(srt=IngestSRT(mode="listener", port=9001, passphrase_env="PASS")),
        packaging=PackagingSpec(ll_hls_path="/live/match-1/index.m3u8"),
        assigned_clients=[client.id],
    )


def test_authorize_ok(client: Client, stream: Stream):
    engine = PolicyEngine({client.id: client}, {stream.id: stream})
    req = SignRequest(client_id=client.id, stream_id=stream.id, use_backup=False, ip="203.0.113.10", country="SE")
    result = engine.authorize(req, ip=req.ip, country=req.country)
    assert result.id == client.id


def test_authorize_denied_ip(client: Client, stream: Stream):
    engine = PolicyEngine({client.id: client}, {stream.id: stream})
    req = SignRequest(client_id=client.id, stream_id=stream.id, use_backup=False, ip="10.0.0.1", country="SE")
    with pytest.raises(AuthorizationError):
        engine.authorize(req, ip=req.ip, country=req.country)


def test_authorize_denied_geo(client: Client, stream: Stream):
    engine = PolicyEngine({client.id: client}, {stream.id: stream})
    req = SignRequest(client_id=client.id, stream_id=stream.id, use_backup=False, ip="203.0.113.10", country="US")
    with pytest.raises(AuthorizationError):
        engine.authorize(req, ip=req.ip, country=req.country)
