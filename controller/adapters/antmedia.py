"""Ant Media Server adapter stub."""
from __future__ import annotations

import logging

from ..core.models import IngestSpec, PlaybackProfile, StreamStats, TokenRules
from .base import AbstractAdapter

logger = logging.getLogger(__name__)


class AntMediaAdapter(AbstractAdapter):
    """Adapter stub for Ant Media Server."""

    async def ensure_input(self, stream_id: str, spec: IngestSpec) -> None:
        logger.info("TODO: implement Ant Media SRT provisioning", extra={"stream_id": stream_id})

    async def ensure_transcode_profile(self, stream_id: str, profile: PlaybackProfile) -> None:
        logger.info("TODO: implement Ant Media transcode profile", extra={"stream_id": stream_id})

    async def ensure_packaging_ll_hls(self, stream_id: str, path: str, profile: PlaybackProfile) -> None:
        logger.info("TODO: implement Ant Media LL-HLS packaging", extra={"stream_id": stream_id})

    async def ensure_token_policy(self, client_id: str, rules: TokenRules) -> None:
        logger.info("TODO: implement Ant Media token policy", extra={"client_id": client_id})

    async def fetch_stats(self, stream_id: str) -> StreamStats:
        logger.info("TODO: implement Ant Media stats fetch", extra={"stream_id": stream_id})
        return StreamStats(stream_id=stream_id, ingest_status="unknown")

    async def delete_stream(self, stream_id: str) -> None:
        logger.info("TODO: implement Ant Media delete", extra={"stream_id": stream_id})
