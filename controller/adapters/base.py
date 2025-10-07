"""Adapter interfaces for interacting with media servers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from ..core.models import IngestSpec, PlaybackProfile, StreamStats, TokenRules


class MediaAdapter(Protocol):
    """Protocol for media server adapters."""

    async def ensure_input(self, stream_id: str, spec: IngestSpec) -> None: ...

    async def ensure_transcode_profile(self, stream_id: str, profile: PlaybackProfile) -> None: ...

    async def ensure_packaging_ll_hls(self, stream_id: str, path: str, profile: PlaybackProfile) -> None: ...

    async def ensure_token_policy(self, client_id: str, rules: TokenRules) -> None: ...

    async def fetch_stats(self, stream_id: str) -> StreamStats: ...

    async def delete_stream(self, stream_id: str) -> None: ...


class AdapterError(RuntimeError):
    """Raised when an adapter call fails."""


class AbstractAdapter(ABC):
    """Base class providing helper utilities for adapters."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @abstractmethod
    async def ensure_input(self, stream_id: str, spec: IngestSpec) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    async def ensure_transcode_profile(self, stream_id: str, profile: PlaybackProfile) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    async def ensure_packaging_ll_hls(self, stream_id: str, path: str, profile: PlaybackProfile) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    async def ensure_token_policy(self, client_id: str, rules: TokenRules) -> None:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    async def fetch_stats(self, stream_id: str) -> StreamStats:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    async def delete_stream(self, stream_id: str) -> None:  # pragma: no cover
        raise NotImplementedError
