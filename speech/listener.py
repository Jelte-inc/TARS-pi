import asyncio
import websockets
import sounddevice as sd
import socket
import threading

# Instellingen
SERVER_URI = "ws://192.168.1.100:8000/audio"   # PC server
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
FRAME_MS = 30
FRAMES = int(SAMPLE_RATE * FRAME_MS / 1000)

running = False

async def stream_audio():
    async with websockets.connect(SERVER_URI, ping_interval=None) as ws:
        print("Connected to PC STT server.")

        def callback(indata, frames, time, status):
            if running:
                asyncio.get_event_loop().call_soon_threadsafe(
                    asyncio.create_task, ws.send(indata.tobytes())
                )

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=FRAMES,
            callback=callback
        ):
            await asyncio.Future()  # keep running

asyncio_loop = asyncio.get_event_loop()

def start_stream():
    global running
    running = True

def stop_stream():
    global running
    running = False

# Eenvoudige lokale TCP server om Python te bedienen (via Flutter)
def control_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 5005))
    s.listen(1)
    print("Control server listening on 5005")

    while True:
        conn, _ = s.accept()
        cmd = conn.recv(1024).decode().strip()

        if cmd == "START":
            start_stream()
            conn.send(b"OK")
        elif cmd == "STOP":
            stop_stream()
            conn.send(b"OK")
        conn.close()

# Start de control server in een thread
threading.Thread(target=control_server, daemon=True).start()

# Start audio stream
asyncio_loop.run_until_complete(stream_audio())
