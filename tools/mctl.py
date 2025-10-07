"""Command-line interface for the media controller."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import httpx
import typer

default_api = os.environ.get("CONTROLLER_API", "http://localhost:8080/v1")

cli = typer.Typer(help="Media controller utilities")


async def _post(path: str, payload: dict | None = None) -> httpx.Response:
    async with httpx.AsyncClient(base_url=default_api) as client:
        return await client.post(path, json=payload)


@cli.command("import-config")
def import_config(config_dir: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Import config YAML files and show summary."""
    from controller.config_loader import load_from_directory

    bundle = load_from_directory(config_dir)
    typer.echo(
        json.dumps(
            {
                "clients": list(bundle.clients.keys()),
                "playback_profiles": list(bundle.playback_profiles.keys()),
                "streams": list(bundle.streams.keys()),
            },
            indent=2,
        )
    )


@cli.command()
def reconcile(stream_id: str) -> None:
    """Trigger reconciliation for a stream via the API."""
    async def _run() -> None:
        resp = await _post(f"/reconcile/{stream_id}")
        resp.raise_for_status()
        typer.echo(resp.json())

    asyncio.run(_run())


@cli.command()
def sign(
    client: str = typer.Option(..., "--client"),
    stream: str = typer.Option(..., "--stream"),
    primary: bool = typer.Option(False, "--primary"),
    backup: bool = typer.Option(False, "--backup"),
) -> None:
    """Sign a playback URL for a client."""
    if primary and backup:
        raise typer.BadParameter("Choose either --primary or --backup")
    use_backup = backup

    async def _run() -> None:
        resp = await _post(
            "/sign",
            {
                "client_id": client,
                "stream_id": stream,
                "use_backup": use_backup,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        typer.echo(data["url"])

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
