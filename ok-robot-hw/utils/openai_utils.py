import cv2
import base64
import json
import matplotlib.pyplot as plt
from termcolor import colored
from tenacity import retry, wait_random_exponential, stop_after_attempt

# Function to capture an image and encode it to base64
def capture_and_encode_image(camera):
    rgb_image, _, _ = camera.capture_image()

    # Rotate the image 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    
    # Display the captured image
    plt.figure(figsize=(10, 10))
    plt.imshow(rgb_image)
    plt.title("Captured Image")
    plt.axis('off')
    plt.show()
    
    _, buffer = cv2.imencode('.jpg', rgb_image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

# Define the navigate_to tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Navigates the robot to a relative position and orientation.",
            "parallel_tool_calls": "false",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "The x coordinate in meters. Positive is forward."},
                    "y": {"type": "number", "description": "The y coordinate in meters. Positive is left"},
                    "theta": {"type": "number", "description": "The orientation angle in radians. Positive is counterclockwise"}
                },
                "required": ["x", "y", "theta"]
            },
            
        }
    },
]

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, client, model="gpt-4o", tools=tools, tool_choice="auto"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def perform_action(hello_robot, response):
    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        print("Tool call detected.")
        available_functions = {
            "navigate_to": navigate_to,
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name in available_functions:
                function = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                xyt_goal = [function_args["x"], function_args["y"], function_args["theta"]]
                function(hello_robot, xyt_goal)
                
    else:
        print("No tool call.")

def navigate_to(robot, xyt_goal):
    print(f"Navigating robot to relative position: x={xyt_goal[0]}, y={xyt_goal[1]}, theta={xyt_goal[2]}")
    robot.robot.nav.navigate_to(xyt_goal, relative=True)

# function not used atm.
def stop():
    print("Stopping.")
    exit