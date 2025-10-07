from datetime import datetime

from controller.core.models import Client, SignRequest, Stream, StreamAdapters, PackagingSpec, IngestSpec, IngestSRT, AdapterSpec
from controller.core.signer import SigningKey, URLSigner


def build_stream() -> Stream:
    adapters = StreamAdapters(
        primary=AdapterSpec(kind="nimble", base_url="https://primary", api_key="k"),
        backup=AdapterSpec(kind="nimble", base_url="https://backup", api_key="k"),
    )
    return Stream(
        id="test-stream",
        description="Test",
        adapters=adapters,
        ingest=IngestSpec(srt=IngestSRT(mode="listener", port=9001, passphrase_env="PASS")),
        packaging=PackagingSpec(ll_hls_path="/live/test-stream/index.m3u8"),
        assigned_clients=["test"],
    )


def build_client() -> Client:
    return Client(
        id="test",
        display_name="Test",
        playback_profile="default",
        token_ttl_seconds=60,
        ip_allowlist=[],
        geo={},
        max_sessions=10,
        watermark={"enabled": False},
    )


def test_sign_and_verify_url():
    signer = URLSigner({"v1": SigningKey(kid="v1", secret=b"secret")})
    stream = build_stream()
    client = build_client()
    request = SignRequest(client_id="test", stream_id="test-stream", use_backup=False)
    expiry = 1700000000
    response = signer.sign(client=client, stream=stream, request=request, expiry=expiry)

    assert "sig=" in response.url
    path_and_query = response.url.split("https://cdn.example")[-1]
    query = path_and_query.split("?")[-1]
    pairs = [tuple(part.split("=")) for part in query.split("&")]
    filtered = [(k, v) for k, v in pairs if k != "sig"]
    signature = next(v for k, v in pairs if k == "sig")
    payload = f"{stream.packaging.ll_hls_path}?" + "&".join(f"{k}={v}" for k, v in filtered)
    assert signer.verify(payload, signature=signature)
