# Player Integration Notes

- Use an LL-HLS capable player (Safari 14+, or hls.js with low-latency mode).
- Ensure the player honors blocking playlists to 2–3 parts in memory to keep latency at 2–5 seconds.
- Provide both primary and backup URLs and switch automatically on failure (HTTP 4xx/5xx or stalled playlist).
- Watermark placeholders `{match_id}` and `{utc_ts}` are populated upstream before signing.
- Tokens expire quickly (60–120s). Refresh the playlist URL periodically.
