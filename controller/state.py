"""Application state container."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Dict

from .adapters.antmedia import AntMediaAdapter
from .adapters.base import MediaAdapter
from .adapters.nimble import NimbleAdapter
from .adapters.wowza import WowzaAdapter
from .config_loader import load_from_directory
from .core.models import AdapterKind, SignRequest
from .core.policy import AuthorizationError, PolicyEngine
from .core.signer import SigningKey, URLSigner
from .repository import Repository
from .workers.reconciler import Reconciler


class AppState:
    """Holds long-lived application components."""

    def __init__(self, config_dir: str | None = None) -> None:
        config_path = Path(config_dir or os.environ.get("CONTROLLER_CONFIG", "config"))
        self.config_bundle = load_from_directory(config_path)
        self.repository = Repository.from_config(self.config_bundle)
        self.policy = PolicyEngine(self.repository.clients, self.repository.streams)
        self.signer = URLSigner({"default": SigningKey(kid="default", secret=os.environ.get("SIGNING_SECRET", "dev-secret").encode())})
        self.adapters: Dict[str, MediaAdapter] = {}
        self._build_adapters()
        self.reconciler = Reconciler(adapters=self.adapters, config=self.config_bundle)
        self._lock = asyncio.Lock()

    def _build_adapters(self) -> None:
        for stream in self.config_bundle.streams.values():
            for label, spec in (("primary", stream.adapters.primary), ("backup", stream.adapters.backup)):
                key = f"{stream.id}:{label}"
                adapter = self._create_adapter(spec)
                self.adapters[key] = adapter

    def _create_adapter(self, spec) -> MediaAdapter:
        if spec.kind == AdapterKind.nimble:
            return NimbleAdapter(spec.base_url, spec.api_key)
        if spec.kind == AdapterKind.wowza:
            return WowzaAdapter(spec.base_url, spec.api_key)
        if spec.kind == AdapterKind.antmedia:
            return AntMediaAdapter(spec.base_url, spec.api_key)
        raise ValueError(f"unsupported adapter kind {spec.kind}")

    async def sign(self, request: SignRequest) -> tuple[str, int, str]:
        stream = self.repository.get_stream(request.stream_id)
        if not stream:
            raise AuthorizationError("unknown_stream")
        client = self.policy.authorize(request, ip=request.ip, country=request.country)
        expiry = self.policy.build_expiry(client)
        result = self.signer.sign(client=client, stream=stream, request=request, expiry=expiry)
        return result.url, result.ttl, result.kid

    async def rotate_key(self, kid: str, secret: str) -> str:
        async with self._lock:
            self.signer.rotate(SigningKey(kid=kid, secret=secret.encode()))
            return kid

    async def reconcile(self, stream_id: str) -> None:
        await self.reconciler.apply(stream_id)

    async def fetch_stats(self, stream_id: str):
        stream = self.repository.get_stream(stream_id)
        if stream is None:
            raise ValueError("stream not found")
        adapter = self.adapters.get(f"{stream_id}:primary")
        if adapter is None:
            raise ValueError("adapter not found")
        return await adapter.fetch_stats(stream_id)

    async def shutdown(self) -> None:
        for adapter in self.adapters.values():
            close = getattr(adapter, "close", None)
            if close:
                await close()
