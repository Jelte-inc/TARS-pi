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
        steps = args.get("steps", 0) # default to 1 step if not provided or 0
    if (direction != None and direction.strip() != "" ):
        match direction.lower():
            case "left":
                servo_controller.move_left(steps)
            case "right":
                servo_controller.move_right(steps)
            case "forward":
                servo_controller.move_forward(steps)
            case "backward":
                servo_controller.move_backward(steps)
                
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

async def handle_text_message(message) -> bool:
    if not isinstance(message, str):
        return False

    try:
        data = json.loads(message)
        print(data)
    except json.JSONDecodeError:
        return False

    await handle_api_data(data)
    return True

async def receiver(websocket):
    #TODO: change this message
    print("Verbonden met command-center.")
    async for message in websocket:
        if not await handle_text_message(message):
            print("Error: Received invalid JSON")

# Main websocket loop
async def text_websocket_task():
    uri = "ws://149.143.35.169:56277/ws"  # pas aan naar je server
    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("Verbonden met command-center.")
        async for message in websocket:
            if not await handle_text_message(message):
                print("Error: Received invalid JSON")
