"""Reconciler job that applies desired state to media adapters."""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, Iterable

from ..adapters.base import MediaAdapter
from ..config_loader import ConfigBundle
from ..core.models import Client, PlaybackProfile, Stream, TokenRules

logger = logging.getLogger(__name__)


class Reconciler:
    """Idempotent reconciler that drives adapters toward the desired state."""

    def __init__(
        self,
        *,
        adapters: Dict[str, MediaAdapter],
        config: ConfigBundle,
    ) -> None:
        self._adapters = adapters
        self._config = config

    async def apply(self, stream_id: str) -> None:
        stream = self._config.streams.get(stream_id)
        if stream is None:
            raise ValueError(f"stream {stream_id} not found")

        profiles = list(self._profiles_for_stream(stream))

        tasks = []
        for label in ("primary", "backup"):
            adapter = self._adapters.get(f"{stream_id}:{label}")
            if adapter is None:
                logger.warning("adapter missing", extra={"stream_id": stream_id, "label": label})
                continue
            for profile in profiles:
                tasks.append(self._reconcile_adapter(adapter, stream, profile))
        if tasks:
            await asyncio.gather(*tasks)

    def _profiles_for_stream(self, stream: Stream) -> Iterable[PlaybackProfile]:
        seen = set()
        for client_id in stream.assigned_clients:
            client = self._config.clients.get(client_id)
            if client is None:
                logger.warning("client missing during reconciliation", extra={"client_id": client_id})
                continue
            profile_name = client.playback_profile
            if profile_name in seen:
                continue
            seen.add(profile_name)
            profile = self._config.playback_profiles.get(profile_name)
            if not profile:
                logger.warning("profile missing during reconciliation", extra={"profile": profile_name})
                continue
            yield profile

    async def _reconcile_adapter(
        self,
        adapter: MediaAdapter,
        stream: Stream,
        profile: PlaybackProfile,
    ) -> None:
        await adapter.ensure_input(stream.id, stream.ingest)
        await adapter.ensure_transcode_profile(stream.id, profile)
        await adapter.ensure_packaging_ll_hls(stream.id, stream.packaging.ll_hls_path, profile)

        for client_id in stream.assigned_clients:
            client: Client | None = self._config.clients.get(client_id)
            if client is None:
                continue
            rules = TokenRules(
                max_sessions=client.max_sessions,
                ttl_seconds=client.token_ttl_seconds,
                path_prefix=f"/live/{stream.id}",
            )
            await adapter.ensure_token_policy(client_id, rules)
