import vlc
import time
import os

def play_audio(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    player = vlc.MediaPlayer(path)
    player.play()

    # allow playback to start
    time.sleep(0.5)

    # wait until playback has finished
    while player.is_playing():
        time.sleep(0.1)

if __name__ == "__main__":
    play_audio("received_audio_files/luvvoice.com-20251202-1McXM8.mp3")
