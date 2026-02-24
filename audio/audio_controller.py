import asyncio
import time
import websockets
import sounddevice as sd
import soundfile as sf
import webrtcvad
import datetime
import io
from pathlib import Path

# =====================
# Audio configuration
# =====================
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

MAX_SILENCE_SEC = 2
MAX_RECORD_SEC = 10.0
MIN_SPEECH_FRAMES = 8  # ~240ms at 30ms frames
startTime = None
RECEIVED_AUDIO_DIR = Path("received_audio")

# =====================
# Audio playback (non-blocking)
# =====================
def decode_audio_buffer(buffer: bytes):
    if not buffer:
        return None, None

    # Server can return WAV bytes or raw PCM16 bytes.
    if buffer.startswith(b"RIFF"):
        data, samplerate = sf.read(io.BytesIO(buffer), dtype="float32")
    else:
        data, samplerate = sf.read(
            io.BytesIO(buffer),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            subtype="PCM_16",
            format="RAW",
            dtype="float32",
        )

    return data, samplerate


async def play_audio(buffer: bytes):
    data, samplerate = decode_audio_buffer(buffer)
    if data is None or samplerate is None:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: sd.play(data, samplerate, blocking=True)
    )


# =====================
# Audio capture + VAD + sending
# =====================
async def capture_and_send_audio(ws, response_complete_event: asyncio.Event):
    global startTime
    vad = webrtcvad.Vad(2)

    silence_limit = int(MAX_SILENCE_SEC * 1000 / FRAME_MS)

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=FRAME_SIZE
    )

    print("Listening loop started")

    with stream:
        while True:
            # Only start listening for a new user utterance when playback is complete.
            await response_complete_event.wait()
            print("Listening...")

            silence_count = 0
            speaking = False
            sent_audio = False
            speech_frames = 0
            pending_frames: list[bytes] = []
            start_time = time.monotonic()

            while True:
                frame, _ = stream.read(FRAME_SIZE)
                frame_bytes = frame.tobytes()

                if time.monotonic() - start_time > MAX_RECORD_SEC:
                    break

                is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)

                if is_speech:
                    speaking = True
                    silence_count = 0
                    speech_frames += 1
                    if not sent_audio:
                        pending_frames.append(frame_bytes)
                        # Don't start a request on tiny noises/clicks.
                        if speech_frames >= MIN_SPEECH_FRAMES:
                            for pending in pending_frames:
                                await ws.send(pending)
                            pending_frames.clear()
                            sent_audio = True
                    else:
                        await ws.send(frame_bytes)

                elif speaking:
                    silence_count += 1
                    if silence_count > silence_limit:
                        break

            if not sent_audio:
                continue

            await ws.send("end")
            now = datetime.datetime.now()
            startTime = now
            print(now.time())
            print("Audio send")
            response_complete_event.clear()


class AudioReceiver:
    def __init__(self, response_complete_event: asyncio.Event | None = None):
        self.response_complete_event = response_complete_event
        self.playback_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.playback_task: asyncio.Task | None = None
        self.finalize_task: asyncio.Task | None = None
        self.is_playing = False

    def _ensure_playback_worker(self):
        if self.playback_task is None or self.playback_task.done():
            self.playback_task = asyncio.create_task(self._playback_worker())

    async def _playback_worker(self):
        while True:
            chunk = await self.playback_queue.get()
            if chunk == b"":
                self.playback_queue.task_done()
                break

            try:
                self.is_playing = True
                self._save_received_audio(chunk)
                await play_audio(chunk)
            except Exception as e:
                print(f"Audio WS: playback failed: {e}")
            finally:
                self.is_playing = False
                self.playback_queue.task_done()

    def _save_received_audio(self, received: bytes):
        RECEIVED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        if received.startswith(b"RIFF"):
            raw_path = RECEIVED_AUDIO_DIR / f"response_{now_str}.wav"
            raw_path.write_bytes(received)
            return

        data, samplerate = decode_audio_buffer(received)
        if data is not None and samplerate is not None:
            wav_path = RECEIVED_AUDIO_DIR / f"response_{now_str}.wav"
            sf.write(str(wav_path), data, samplerate)

    async def _finalize_response_after_playback(self):
        await self.playback_queue.join()
        while self.is_playing:
            await asyncio.sleep(0.01)
        if self.response_complete_event is not None:
            self.response_complete_event.set()

    async def close(self):
        if self.finalize_task is not None:
            self.finalize_task.cancel()
            try:
                await self.finalize_task
            except asyncio.CancelledError:
                pass

        if self.playback_task is not None and not self.playback_task.done():
            await self.playback_queue.put(b"")
            await self.playback_task

    async def handle_message(self, message) -> bool:
        if isinstance(message, bytes):
            self._ensure_playback_worker()
            await self.playback_queue.put(bytes(message))
            return True

        if isinstance(message, str) and message.lower() == "end":
            now = datetime.datetime.now()
            if startTime is not None:
                duration = now - startTime
                seconds = duration.total_seconds() # Dit geeft de tijd in seconden
                print(f"Ontvangen op: {now.time()}")
                print(f"Totale duratie (latency): {seconds:.3f} seconden")
            else:
                print(f"Ontvangen op: {now.time()}")
                print("Totale duratie (latency): onbekend (geen starttijd)")

            if self.finalize_task is not None and not self.finalize_task.done():
                self.finalize_task.cancel()
            self.finalize_task = asyncio.create_task(self._finalize_response_after_playback())
            return True

        return False


# =====================
# Websocket task
# =====================
import asyncio
import websockets


async def audio_websocket_task():
    uri = "ws://149.143.35.169:56277/ws"

    while True:
        response_complete_event = asyncio.Event()
        response_complete_event.set()
        receiver = AudioReceiver(response_complete_event)
        sender_task = None

        try:
            print("Audio WS: attempting to connect...")

            async with websockets.connect(uri, open_timeout=5) as ws:
                print("Audio WS: connected")

                # Start audio capture + sending task
                sender_task = asyncio.create_task(capture_and_send_audio(ws, response_complete_event))

                async for message in ws:
                    await receiver.handle_message(message)

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
            await receiver.close()

            print("Audio WS: disconnected, retrying in 2 seconds")
            await asyncio.sleep(2)
