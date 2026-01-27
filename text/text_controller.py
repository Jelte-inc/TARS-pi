import asyncio
import websockets
import json

# Actions
async def move_action(args):
    direction = args.get("direction")
    print(f"Executing MOVE: Going {direction}...")

async def handle_command(data):
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
    print("Verbonden met command-center.")
    async for message in websocket:
        try:
            # Parse de JSON stream
            data = json.loads(message)
            await handle_command(data)
            
        except json.JSONDecodeError:
            print("Error: Received invalid JSON")

# Main websocket loop
async def main():
    async with websockets.serve(receiver, "0.0.0.0", 8765, ping_interval=None):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())