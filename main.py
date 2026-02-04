from text.text_controller import text_websocket_task
from audio.audio_controller import audio_websocket_task
import asyncio


async def main():
    ws1 = asyncio.create_task(text_websocket_task())
    ws2 = asyncio.create_task(audio_websocket_task())

    # Wacht tot beide taken klaar zijn (in praktijk: nooit)
    await asyncio.gather(ws1, ws2)

if __name__ == "__main__":
    asyncio.run(main())
