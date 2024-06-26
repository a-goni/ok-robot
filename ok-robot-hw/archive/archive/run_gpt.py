import os
import time
import signal
import zmq
import json
from openai import OpenAI
from camera import RealSenseCamera
from utils.navigation_utils import run_navigation_gpt, load_offset
from utils.manipulation_utils import run_manipulation_gpt, run_place_gpt
from utils.asier_utils import signal_handler, capture_and_encode_image
from robot import HelloRobot
from args import get_args2
from global_parameters import *

# OpenAI API setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o"

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
                    "text_A": {"type": "string", "description": "Target object to navigate to. This must be an object in the scene."},
                    "text_B": {"type": "string", "description": "Reference object to help localisation. Another object in the scene."}
                },
                "required": ["text_A"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_manipulation",
            "description": "Manipulate the robot to pick up a specified object",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Object to pick-up (manipulate)"}
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
            "content":
            """
            I am a mobile service robot in a home environment. My task is to look after the apartment and keep it clean and tidy.
            I have a mobile base, robotic arm and a camera. My available actions are run_navigation, run_manipulation, and run_place.
            I will receive an image input, and from this, I will respond with a function_call or tool_call utilising the provided tools, run_navigation, run_manipulation, and run_place. 
            I will be specific about the object from what I see in the image scene.
            The user cannot be spoken to.
            """
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Initial image taken on wake up."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                }
            ]
        }
    ]
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        tools=tools,
        max_tokens=200
    )

    # Print the assistant's message content to the console
    print("GPT Response:", response)
    if hasattr(response, "choices") and response.choices:
        for choice in response.choices:
            if "message" in choice:
                print("GPT Suggested Actions:", choice.message.get("content", "No content in the response"))
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    print("Tool Calls:")
                    for tool_call in choice.message.tool_calls:
                        print(f"Function Name: {tool_call.function.name}")
                        print(f"Arguments: {tool_call.function.arguments}")
            else:
                print("No message found in choice")
    else:
        print("No choices found in the response")
    
    return response

def run():
    args = get_args2() 
    load_offset(args.x1, args.y1, args.x2, args.y2)
    hello_robot = HelloRobot(end_link=GRIPPER_MID_NODE)
    camera = RealSenseCamera(hello_robot.robot)

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
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        print("Function: ", function_name)
                        print("Arguments: ", arguments)
                        if function_name == "run_navigation":
                            run_navigation_gpt(hello_robot.robot, nav_socket, arguments["text_A"], arguments.get("text_B"))
                        elif function_name == "run_manipulation":
                            run_manipulation_gpt(hello_robot, anygrasp_socket, arguments["text"], TOP_CAMERA_NODE, GRIPPER_MID_NODE)
                        elif function_name == "run_place":
                            run_place_gpt(hello_robot, anygrasp_socket, arguments["text"], TOP_CAMERA_NODE, GRIPPER_MID_NODE)

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()