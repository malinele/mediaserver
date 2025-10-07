"""Policy evaluation for playback authorization."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .models import Client, SignRequest, Stream


class AuthorizationError(Exception):
    """Raised when a request does not satisfy policy checks."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class PolicyEngine:
    """Evaluates per-client playback policies."""

    def __init__(self, clients: Dict[str, Client], streams: Dict[str, Stream]):
        self._clients = clients
        self._streams = streams

    def authorize(self, req: SignRequest, *, ip: Optional[str], country: Optional[str]) -> Client:
        client = self._clients.get(req.client_id)
        if client is None:
            raise AuthorizationError("unknown_client")

        stream = self._streams.get(req.stream_id)
        if stream is None:
            raise AuthorizationError("unknown_stream")

        if req.client_id not in stream.assigned_clients:
            raise AuthorizationError("client_not_assigned")

        if ip and not client.is_ip_allowed(ip):
            raise AuthorizationError("ip_not_allowed")

        if not client.is_geo_allowed(country):
            raise AuthorizationError("geo_not_allowed")

        return client

    @staticmethod
    def build_expiry(client: Client, *, now: Optional[datetime] = None) -> int:
        return int(client.token_expiry(now).timestamp())
