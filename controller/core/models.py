"""Domain models for the media controller."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from ipaddress import ip_network, ip_address
from typing import Dict, Iterable, List, Optional


def _uppercase_list(values: Optional[Iterable[str]]) -> Optional[List[str]]:
    if values is None:
        return None
    return [v.upper() for v in values]


@dataclass
class GeoPolicy:
    allow_countries: Optional[List[str]] = None
    deny_countries: Optional[List[str]] = None

    def __post_init__(self) -> None:
        self.allow_countries = _uppercase_list(self.allow_countries)
        self.deny_countries = _uppercase_list(self.deny_countries)


@dataclass
class Watermark:
    enabled: bool = False
    template: Optional[str] = None


@dataclass
class Client:
    id: str
    display_name: str
    playback_profile: str
    token_ttl_seconds: int
    ip_allowlist: List[str] = field(default_factory=list)
    geo: GeoPolicy = field(default_factory=GeoPolicy)
    max_sessions: int = 1
    watermark: Watermark = field(default_factory=Watermark)

    def __post_init__(self) -> None:
        if isinstance(self.geo, dict):
            self.geo = GeoPolicy(**self.geo)
        if isinstance(self.watermark, dict):
            self.watermark = Watermark(**self.watermark)

    def is_ip_allowed(self, ip: str) -> bool:
        if not self.ip_allowlist:
            return True
        target = ip_address(ip)
        for cidr in self.ip_allowlist:
            if target in ip_network(cidr):
                return True
        return False

    def is_geo_allowed(self, country_code: Optional[str]) -> bool:
        if country_code is None:
            return not self.geo.allow_countries
        country_code = country_code.upper()
        if self.geo.deny_countries and country_code in self.geo.deny_countries:
            return False
        if self.geo.allow_countries:
            return country_code in self.geo.allow_countries
        return True

    def token_expiry(self, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.utcnow()
        return now + timedelta(seconds=self.token_ttl_seconds)


@dataclass
class Rendition:
    name: str
    w: int
    h: int
    kbps: int
    fps: int

    @classmethod
    def from_dict(cls, data: Dict) -> "Rendition":
        return cls(**data)


@dataclass
class PlaybackProfile:
    name: str
    gop_seconds: float
    parts_seconds: float
    segment_seconds: float
    renditions: List[Rendition]

    def __post_init__(self) -> None:
        self.renditions = [r if isinstance(r, Rendition) else Rendition.from_dict(r) for r in self.renditions]


class AdapterKind(str, Enum):
    nimble = "nimble"
    wowza = "wowza"
    antmedia = "antmedia"


@dataclass
class AdapterSpec:
    kind: AdapterKind
    base_url: str
    api_key: str

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = AdapterKind(self.kind)


@dataclass
class IngestSRT:
    mode: str
    port: int
    passphrase_env: str


@dataclass
class IngestSpec:
    srt: IngestSRT

    def __post_init__(self) -> None:
        if isinstance(self.srt, dict):
            self.srt = IngestSRT(**self.srt)


@dataclass
class PackagingSpec:
    ll_hls_path: str


@dataclass
class StreamAdapters:
    primary: AdapterSpec
    backup: AdapterSpec

    def __post_init__(self) -> None:
        if isinstance(self.primary, dict):
            self.primary = AdapterSpec(**self.primary)
        if isinstance(self.backup, dict):
            self.backup = AdapterSpec(**self.backup)


@dataclass
class Stream:
    id: str
    description: Optional[str]
    adapters: StreamAdapters
    ingest: IngestSpec
    packaging: PackagingSpec
    assigned_clients: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.adapters, dict):
            self.adapters = StreamAdapters(**self.adapters)
        if isinstance(self.ingest, dict):
            self.ingest = IngestSpec(**self.ingest)
        if isinstance(self.packaging, dict):
            self.packaging = PackagingSpec(**self.packaging)


@dataclass
class TokenRules:
    max_sessions: int
    ttl_seconds: int
    path_prefix: str


@dataclass
class SignedURL:
    url: str
    ttl: int


@dataclass
class SignRequest:
    client_id: str
    stream_id: str
    use_backup: bool = False
    ip: Optional[str] = None
    country: Optional[str] = None


@dataclass
class SignResponse:
    url: str
    ttl: int
    kid: str


@dataclass
class StreamStats:
    stream_id: str
    ingest_status: str
    last_part_age_seconds: Optional[float] = None
    last_segment_age_seconds: Optional[float] = None
    cpu_percent: Optional[float] = None
    http_error_rate: Optional[float] = None
    renditions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    error: Optional[str] = None
