"""Simple in-memory repositories for controller entities."""
from __future__ import annotations

from typing import Dict, Optional

from .core.models import Client, PlaybackProfile, Stream


class Repository:
    """In-memory repository seeded from configuration."""

    def __init__(self) -> None:
        self.clients: Dict[str, Client] = {}
        self.playback_profiles: Dict[str, PlaybackProfile] = {}
        self.streams: Dict[str, Stream] = {}

    def add_client(self, client: Client) -> None:
        self.clients[client.id] = client

    def get_client(self, client_id: str) -> Optional[Client]:
        return self.clients.get(client_id)

    def add_playback_profile(self, profile: PlaybackProfile) -> None:
        self.playback_profiles[profile.name] = profile

    def get_playback_profile(self, name: str) -> Optional[PlaybackProfile]:
        return self.playback_profiles.get(name)

    def add_stream(self, stream: Stream) -> None:
        self.streams[stream.id] = stream

    def get_stream(self, stream_id: str) -> Optional[Stream]:
        return self.streams.get(stream_id)

    @classmethod
    def from_config(cls, bundle) -> "Repository":
        repo = cls()
        for client in bundle.clients.values():
            repo.add_client(client)
        for profile in bundle.playback_profiles.values():
            repo.add_playback_profile(profile)
        for stream in bundle.streams.values():
            repo.add_stream(stream)
        return repo
