import board
import busio
import adafruit_pca9685
from adafruit_servokit import ServoKit
import time

###CONFIG###
kit = ServoKit(channels=16)
left_motor = kit.servo[0]
right_motor = kit.servo[1]
up_and_down_motor_one = kit.servo[2]

###INIT###

# Set the left and right motors to a 90 degree angle to make room for backward movement
left_motor.angle = 90
right_motor.angle = 90

#set the up and down motors to 0 for maximum range
up_and_down_motor_one.angle = 0

###WALKING FUNCTIONS###
def move_left(given_steps:int):
    handled_steps = 0 
    while handled_steps < given_steps:
        print("step:", handled_steps ,"of", given_steps)
        handled_steps += 1
        up_and_down_motor_one.angle = 90
        time.sleep(2)
        right_motor.angle = 135
        time.sleep(2)
        up_and_down_motor_one.angle = 0
        time.sleep(2)
        right_motor.angle = 90
        if (given_steps > 1):
            time.sleep(2)

def move_right(given_steps:int):
    handled_steps = 0 
    while handled_steps < given_steps:
        print("step:", handled_steps ,"of", given_steps)
        handled_steps += 1
        up_and_down_motor_one.angle = 90
        time.sleep(2)
        left_motor.angle = 135
        time.sleep(2)
        up_and_down_motor_one.angle = 0
        time.sleep(2)
        left_motor.angle = 90
        if (given_steps > 1):
            time.sleep(2)

def move_forward(given_steps:int):
    handled_steps = 0 
    while handled_steps < given_steps:
        print("step:", handled_steps ,"of", given_steps)
        handled_steps += 1
        up_and_down_motor_one.angle = 90
        time.sleep(2)
        left_motor.angle = 135
        right_motor.angle = 135
        time.sleep(2)
        up_and_down_motor_one.angle = 0
        time.sleep(2)
        left_motor.angle = 90
        right_motor.angle = 90
        if (given_steps > 1):
            time.sleep(2)

def move_backward(given_steps:int):
    handled_steps = 0
    while handled_steps < given_steps:
        print("step:", handled_steps ,"of", given_steps)
        handled_steps += 1
        print("moving legs up")
        up_and_down_motor_one.angle = 90
        time.sleep(2)
        print("moving the left and right leg backward")
        left_motor.angle = 45
        right_motor.angle = 45
        time.sleep(2)
        print("moving the legs down")
        up_and_down_motor_one.angle = 0
        time.sleep(2)
        print("moving the left and right leg to original position")
        left_motor.angle = 90
        right_motor.angle = 90
        if (given_steps > 1):
            time.sleep(2)
