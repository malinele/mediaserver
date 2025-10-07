# OBS / vMix Setup Guide

1. Configure an SRT output targeting the primary Nimble listener:
   - URL: `srt://<nimble-a-ip>:9001?mode=caller`
   - Passphrase: obtain from operations secret store (`SRT_PASSPHRASE`).
2. Add the backup Nimble listener as a secondary output with identical encoding settings.
3. Video encoding:
   - Codec: H.264
   - Resolution: 1920x1080 or as required by the event
   - Frame rate: 30 fps
   - Keyframe interval: 2 seconds
   - Bitrate: 6 Mbps CBR
4. Audio encoding:
   - Codec: AAC
   - Bitrate: 128–160 kbps
   - Sample rate: 48 kHz
5. Before going live, verify ingest status on the controller admin page (`/v1/admin`).
6. Keep OBS/vMix running during failover drills to ensure both Nimble nodes ingest the stream.
