import board
import busio
import adafruit_pca9685
from adafruit_servokit import ServoKit
import time

###CONFIG###
kit = ServoKit(channels=16)
servo1 = kit.servo[1]
servo2 = kit.servo[2]

###INIT###
servo1.angle = 90
servo2.angle = 90