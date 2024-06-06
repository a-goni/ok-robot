import os
import cv2
import time
import signal
import zmq
import base64
import json
from openai import OpenAI
from camera import RealSenseCamera
from utils.navigation_utils import run_navigation
from utils.manipulation_utils import run_manipulation, run_place
from utils.asier_utils import signal_handler
from robot import HelloRobot
from args import get_args2
from global_parameters import *

# OpenAI API setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o"

# Function to capture an image and encode it to base64
def capture_and_encode_image(camera):
    rgb_image, _, _ = camera.capture_image()
    _, buffer = cv2.imencode('.jpg', rgb_image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

# Define tools for GPT
tools = [
    {
        "type": "function",
        "function": {
            "name": "run_navigation",
            "description": "Navigate the robot to the specified location",
            "parameters": {
                "type": "object",
                "properties": {
                    "A": {"type": "string", "description": "Target object to navigate to"},
                    "B": {"type": "string", "description": "Reference object to help localization"}
                },
                "required": ["A"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_manipulation",
            "description": "Manipulate the robot to pick up specified objects",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Object to manipulate"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_place",
            "description": "Place the object held by the robot at the specified location",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Target place to put the object"}
                },
                "required": ["text"]
            }
        }
    }
]

# Function to send image to GPT and get actions
def get_gpt_actions(encoded_image):
    messages = [
        {
            "role": "system",
            "content": "You are an assistive cleaning robot. You have a mobile base and robotic arm, which allows you to navigate, pick up objects, and place objects. Given the image, decide what the next best steps are to clean the area."
        },
        {
            "role": "user",
            "content": f"data:image/jpeg;base64,{encoded_image}"
        }
    ]
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function"}
    )
    return response

def run():
    args = get_args2()
    hello_robot = HelloRobot()
    camera = RealSenseCamera(hello_robot)

    context = zmq.Context()
    nav_socket = context.socket(zmq.REQ)
    nav_socket.connect("tcp://" + args.ipw + ":" + str(args.navigation_port))
    anygrasp_socket = context.socket(zmq.REQ)
    anygrasp_socket.connect("tcp://" + args.ipc + ":" + str(args.manipulation_port))

    while True:
        try:
            encoded_image = capture_and_encode_image(camera)
            gpt_response = get_gpt_actions(encoded_image)
            
            for choice in gpt_response.choices:
                if "tool_calls" in choice.message:
                    for tool_call in choice.message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        if function_name == "run_navigation":
                            run_navigation(hello_robot.robot, nav_socket, arguments["A"], arguments.get("B"))
                        elif function_name == "run_manipulation":
                            run_manipulation(hello_robot, anygrasp_socket, arguments["text"], TOP_CAMERA_NODE, GRIPPER_MID_NODE)
                        elif function_name == "run_place":
                            run_place(hello_robot, anygrasp_socket, arguments["text"], TOP_CAMERA_NODE, GRIPPER_MID_NODE)

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()