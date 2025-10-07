"""Helpers to load controller configuration from YAML."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from .core.models import Client, PlaybackProfile, Stream


class ConfigBundle:
    """Container for parsed configuration data."""

    def __init__(self, clients: List[Client], profiles: List[PlaybackProfile], streams: List[Stream]):
        self.clients = {client.id: client for client in clients}
        self.playback_profiles = {profile.name: profile for profile in profiles}
        self.streams = {stream.id: stream for stream in streams}

    def get_client(self, client_id: str) -> Client:
        return self.clients[client_id]

    def get_profile(self, profile_name: str) -> PlaybackProfile:
        return self.playback_profiles[profile_name]

    def get_stream(self, stream_id: str) -> Stream:
        return self.streams[stream_id]


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def load_from_directory(config_dir: Path) -> ConfigBundle:
    clients_raw = _load_yaml(config_dir / "clients.yaml")
    profiles_raw = _load_yaml(config_dir / "playback_profiles.yaml")
    streams_raw = _load_yaml(config_dir / "streams.yaml")

    clients = [Client(**data) for data in clients_raw["clients"]]
    profiles = [PlaybackProfile(**data) for data in profiles_raw["profiles"]]
    streams = [Stream(**data) for data in streams_raw["streams"]]

    return ConfigBundle(clients, profiles, streams)
