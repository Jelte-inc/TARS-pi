import asyncio
import time
import websockets
import sounddevice as sd
import soundfile as sf
import webrtcvad

# =====================
# Audio configuration
# =====================
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

MAX_SILENCE_SEC = 0.8
MAX_RECORD_SEC = 10.0


# =====================
# Audio playback (non-blocking)
# =====================
async def play_audio(buffer: bytes):
    if not buffer:
        return

    with open("debug.wav", "wb") as f:
        f.write(buffer)

    data, samplerate = sf.read("debug.wav", dtype="float32")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: sd.play(data, samplerate, blocking=True)
    )


# =====================
# Audio capture + VAD + sending
# =====================
async def capture_and_send_audio(ws):
    vad = webrtcvad.Vad(2)

    silence_limit = int(MAX_SILENCE_SEC * 1000 / FRAME_MS)
    silence_count = 0
    speaking = False
    start_time = time.monotonic()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=FRAME_SIZE
    )

    print("Listening...")

    with stream:
        while True:
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = frame.tobytes()

            if time.monotonic() - start_time > MAX_RECORD_SEC:
                break

            is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)

            if is_speech:
                speaking = True
                silence_count = 0
                await ws.send(frame_bytes)

            elif speaking:
                silence_count += 1
                if silence_count > silence_limit:
                    break

    await ws.send("end")
    print("Audio send")


# =====================
# Websocket task
# =====================
import asyncio
import websockets


async def audio_websocket_task():
    uri = "ws://149.143.35.169:56277/ws"

    while True:
        audio_buffer = bytearray()
        sender_task = None

        try:
            print("Audio WS: attempting to connect...")

            async with websockets.connect(uri, open_timeout=5) as ws:
                print("Audio WS: connected")

                # Start audio capture + sending task
                sender_task = asyncio.create_task(capture_and_send_audio(ws))

                async for message in ws:
                    if isinstance(message, bytes):
                        audio_buffer.extend(message)

                    elif isinstance(message, str) and message.lower() == "end":
                        print("Audio WS: audio received, playing back")
                        await play_audio(bytes(audio_buffer))
                        audio_buffer.clear()

        except asyncio.TimeoutError:
            print("Audio WS: connection timed out")

        except OSError as e:
            print(f"Audio WS: network error: {e}")

        except Exception as e:
            print(f"Audio WS: unexpected error: {e}")

        finally:
            # Ensure sender task is stopped on disconnect
            if sender_task is not None:
                sender_task.cancel()
                try:
                    await sender_task
                except asyncio.CancelledError:
                    pass

            print("Audio WS: disconnected, retrying in 2 seconds")
            await asyncio.sleep(2)
