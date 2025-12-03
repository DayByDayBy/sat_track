#!/usr/bin/env uv run
"""Simple WebSocket client to test /ws/satellites streaming."""

import asyncio
import json
import websockets


async def client():
    uri = "ws://127.0.0.1:8000/ws/satellites"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to", uri)
            count = 0
            async for message in websocket:
                data = json.loads(message)
                last_updated = data.get("last_updated")
                satellites = data.get("satellites", {})
                print(f"[{count}] last_updated={last_updated}, satellites={len(satellites)}")
                # Optionally print a few entries:
                if satellites:
                    sample_name, sample_pos = next(iter(satellites.items()))
                    print(f"  sample: {sample_name} lat={sample_pos['lat']:.2f}, lon={sample_pos['lon']:.2f}")
                count += 1
                if count >= 5:
                    print("Stopping after 5 messages.")
                    break
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    asyncio.run(client())
