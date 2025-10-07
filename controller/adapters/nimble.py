"""Nimble Streamer adapter implementation."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable

import httpx

from ..core.models import IngestSpec, PlaybackProfile, StreamStats, TokenRules
from .base import AbstractAdapter, AdapterError

logger = logging.getLogger(__name__)


class NimbleAdapter(AbstractAdapter):
    """Adapter that manages resources on a Nimble Streamer node."""

    def __init__(self, base_url: str, api_key: str, *, timeout: float = 10.0):
        super().__init__(base_url, api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"X-API-KEY": api_key},
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        ok_status: Iterable[int] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        ok_status = tuple(ok_status or (200, 201, 202, 204))
        try:
            resp = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:  # pragma: no cover - network failure path
            logger.error("nimble request error", exc_info=exc)
            raise AdapterError("nimble connection error") from exc
        if resp.status_code not in ok_status:
            logger.error(
                "nimble error %s %s", resp.status_code, resp.text[:500]
            )
            raise AdapterError(f"nimble request failed: {resp.status_code}")
        return resp

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._request("POST", path, json=payload)
        return resp.json()

    async def ensure_input(self, stream_id: str, spec: IngestSpec) -> None:
        payload = {
            "id": stream_id,
            "type": "srt_listener",
            "port": spec.srt.port,
            "passphrase": f"env:{spec.srt.passphrase_env}",
        }
        logger.debug("ensuring Nimble input", extra={"stream_id": stream_id, "payload": payload})
        await self._post("/api/inputs", payload)

    async def ensure_transcode_profile(self, stream_id: str, profile: PlaybackProfile) -> None:
        payload = {
            "stream_id": stream_id,
            "gop": profile.gop_seconds,
            "renditions": [
                {
                    "name": rendition.name,
                    "width": rendition.w,
                    "height": rendition.h,
                    "bitrate_kbps": rendition.kbps,
                    "fps": rendition.fps,
                }
                for rendition in profile.renditions
            ],
        }
        logger.debug("ensuring Nimble transcode", extra={"stream_id": stream_id})
        await self._post("/api/transcode", payload)

    async def ensure_packaging_ll_hls(self, stream_id: str, path: str, profile: PlaybackProfile) -> None:
        payload = {
            "stream_id": stream_id,
            "output_path": path,
            "segment_seconds": profile.segment_seconds,
            "part_seconds": profile.parts_seconds,
            "low_latency": True,
        }
        logger.debug("ensuring Nimble LL-HLS", extra={"stream_id": stream_id})
        await self._post("/api/packaging/ll-hls", payload)

    async def ensure_token_policy(self, client_id: str, rules: TokenRules) -> None:
        payload = {
            "client_id": client_id,
            "max_sessions": rules.max_sessions,
            "ttl": rules.ttl_seconds,
            "path_prefix": rules.path_prefix,
        }
        logger.debug("ensuring Nimble token policy", extra={"client_id": client_id})
        await self._post("/api/token-policy", payload)

    async def fetch_stats(self, stream_id: str) -> StreamStats:
        resp = await self._request("GET", f"/api/streams/{stream_id}/stats")
        data = resp.json()
        return StreamStats(
            stream_id=stream_id,
            ingest_status=data.get("ingest_status", "unknown"),
            last_part_age_seconds=data.get("part_age"),
            last_segment_age_seconds=data.get("segment_age"),
            cpu_percent=data.get("cpu"),
            http_error_rate=data.get("http_errors"),
            renditions=data.get("renditions", {}),
        )

    async def delete_stream(self, stream_id: str) -> None:
        await self._request(
            "DELETE",
            f"/api/streams/{stream_id}",
            ok_status=(200, 204, 404),
        )

    async def close(self) -> None:
        await self._client.aclose()
