import asyncio
import json
import os
import sys

import websockets

# Ensure project root is on the path so sibling packages (e.g., servos) can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import servos.servo_controller as servo_controller

# Actions
async def move_action(args):
    direction = args.get("direction")
    steps = args.get("steps")
    if(steps == 0):
        Exception("NO STEPS GIVEN")
        #TODO: switch case
    if (direction != None and direction.strip() != "" ):
        if (direction == "left"):
            servo_controller.move_left(given_steps=args.get("steps"))    
        if (direction == "right"):
            servo_controller.move_right(given_steps=args.get("steps"))
        if (direction == "forward"):
            servo_controller.move_forward(given_steps=args.get("steps"))
        if (direction == "backward"):
            servo_controller.move_backward(given_steps=args.get("steps"))

    print(f"Executing MOVE: Going {direction}...")

async def handle_api_data(data):
    command = data.get("command")
    args = data.get("args", {})
    speech = data.get("speech")

    # if speech data is included send to front-end
    if speech:
        print(f"System says: '{speech}'")
    #TODO: Send speech data to front-end

    # Handle commands
    if command == "move":
        await move_action(args)
    #TODO: Add more options for commands
    # elif command == "stop":
    #     print("Stopping all actions.")
    else:
        print(f"Unknown command: {command}; Skipping actions")

async def receiver(websocket):
    #TODO: change this message
    print("Verbonden met command-center.")
    async for message in websocket:
        try:
            # Parse de JSON stream
            data = json.loads(message)
            await handle_api_data(data)
            
        except json.JSONDecodeError:
            print("Error: Received invalid JSON")

# Main websocket loop
async def text_websocket_task():
    async with websockets.serve(receiver, "0.0.0.0", 8765, ping_interval=None):
        await asyncio.Future()
