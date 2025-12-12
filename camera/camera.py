from picamera2 import Picamera2
from datetime import datetime

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
picam2.capture_file(filename)

print("Opgeslagen als:", filename)
