import websocket
import sounddevice as sd
import soundfile as sf
import webrtcvad
import time

audio_buffer = bytearray()

def on_message(ws, message):
    global audio_buffer

    if isinstance(message, bytes):
        audio_buffer.extend(message)

    elif isinstance(message, str) and message.lower() == "end":
        print("Length of audio_buffer:", len(audio_buffer))

        if not audio_buffer:
            print("Geen audio ontvangen!")
            return

        with open("debug.wav", "wb") as f:
            f.write(audio_buffer)

        data, samplerate = sf.read("debug.wav", dtype="float32")
        sd.play(data, samplerate=samplerate, blocking=True)

        print("Audio volledig afgespeeld")
        audio_buffer = bytearray()


def on_error(ws, error):
    print("WebSocket error:", error)


def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")


def on_open(ws):
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FRAME_MS = 30
    FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

    MAX_SILENCE_SEC = 0.8
    MAX_RECORD_SEC = 10.0   # harde limiet

    vad = webrtcvad.Vad(2)
    silence_limit = int(MAX_SILENCE_SEC * 1000 / FRAME_MS)

    silence_count = 0
    speaking = False
    start_time = time.monotonic()

    print("Luisteren... spreek nu")

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=FRAME_SIZE
    )

    with stream:
        while True:
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = frame.tobytes()

            elapsed = time.monotonic() - start_time
            if elapsed >= MAX_RECORD_SEC:
                print("Maximale opnameduur bereikt")
                break

            is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)

            if is_speech:
                if not speaking:
                    print("Spraak gedetecteerd, verzenden")
                    speaking = True

                silence_count = 0
                ws.send(frame_bytes, opcode=websocket.ABNF.OPCODE_BINARY)

            elif speaking:
                silence_count += 1
                if silence_count > silence_limit:
                    print("Stilte gedetecteerd, stoppen")
                    break

    ws.send("end")

ws = websocket.WebSocketApp(
    "ws://149.143.35.169:56277/ws",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
