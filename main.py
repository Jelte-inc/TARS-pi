import asyncio
import websockets

from text.text_controller import handle_text_message
from audio.audio_controller import AudioReceiver, capture_and_send_audio


async def unified_websocket_task():
    uri = "ws://149.143.35.169:56277/ws"

    while True:
        response_complete_event = asyncio.Event()
        response_complete_event.set()
        receiver = AudioReceiver(response_complete_event)
        sender_task = None
        should_retry = True

        try:
            print("WS: attempting to connect...")

            async with websockets.connect(uri, open_timeout=5, ping_interval=None) as ws:
                print("WS: connected")

                sender_task = asyncio.create_task(capture_and_send_audio(ws, response_complete_event))

                async for message in ws:
                    handled_text = await handle_text_message(message)
                    if handled_text:
                        continue

                    handled_audio = await receiver.handle_message(message)
                    if not handled_audio:
                        print("WS: received unknown message type")

        except asyncio.TimeoutError:
            print("WS: connection timed out")

        except OSError as e:
            print(f"WS: network error: {e}")

        except asyncio.CancelledError:
            print("WS: shutdown requested")
            should_retry = False
            return

        except Exception as e:
            print(f"WS: unexpected error: {e}")

        finally:
            if sender_task is not None:
                sender_task.cancel()
                try:
                    await sender_task
                except asyncio.CancelledError:
                    pass
                except BaseException:
                    pass
            await receiver.close()

        if not should_retry:
            return

        print("WS: disconnected, retrying in 2 seconds")
        await asyncio.sleep(2)


async def main():
    await unified_websocket_task()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
