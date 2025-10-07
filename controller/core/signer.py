"""URL signing utilities."""
from __future__ import annotations

import base64
import hmac
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict
from urllib.parse import urlencode, urljoin

from .models import Client, SignRequest, SignResponse, Stream


@dataclass
class SigningKey:
    kid: str
    secret: bytes

    @classmethod
    def from_env(cls, kid_env: str, secret_env: str) -> "SigningKey":
        kid = os.environ[kid_env]
        secret = os.environ[secret_env].encode()
        return cls(kid=kid, secret=secret)


class URLSigner:
    """Signs LL-HLS playlists and segments."""

    def __init__(self, keys: Dict[str, SigningKey]) -> None:
        if not keys:
            raise ValueError("at least one signing key is required")
        self._keys = keys
        self._current_kid = max(keys.keys())

    @property
    def current_key(self) -> SigningKey:
        return self._keys[self._current_kid]

    def rotate(self, key: SigningKey) -> None:
        self._keys[key.kid] = key
        self._current_kid = key.kid

    def sign(self, *, client: Client, stream: Stream, request: SignRequest, expiry: int) -> SignResponse:
        base_path = stream.packaging.ll_hls_path
        path = f"/live/{stream.id}/index.m3u8" if not base_path else base_path
        params = {
            "client": client.id,
            "exp": str(expiry),
            "kid": self.current_key.kid,
        }
        if request.use_backup:
            params["backup"] = "1"
        query = urlencode(params)
        to_sign = f"{path}?{query}".encode()
        signature = hmac.new(self.current_key.secret, to_sign, sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
        params["sig"] = sig_b64
        url = urljoin("https://cdn.example", f"{path}?{urlencode(params)}")
        return SignResponse(url=url, ttl=client.token_ttl_seconds, kid=self.current_key.kid)

    def verify(self, url_path: str, *, signature: str) -> bool:
        expected = hmac.new(self.current_key.secret, url_path.encode(), sha256).digest()
        padding = "=" * (-len(signature) % 4)
        provided = base64.urlsafe_b64decode(signature + padding)
        return hmac.compare_digest(expected, provided)
