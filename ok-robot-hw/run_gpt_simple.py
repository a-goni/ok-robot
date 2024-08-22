import os
import signal
from utils.asier_utils import signal_handler
from utils.openai_utils import (
    capture_images,
    chat_completion_request, 
    perform_action,
)
from utils.messages_utils import add_system_message
from openai import OpenAI
from robot import HelloRobot
from camera import RealSenseCamera
from wide_camera import WideCamera

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o"

def run():
    hello_robot = HelloRobot()
    camera = RealSenseCamera(hello_robot.robot)
    wide_camera = WideCamera()
    hello_robot.robot.move_to_new_nav_posture()
    hello_robot.robot.head.look_front()
    messages = []
    messages = add_system_message(messages)

    while True:
        try:
            # possible views ['RGB', 'Depth', 'WideDown', 'WideGripper', 'Map']
            views = ['WideDown', 'WideGripper', 'Map']
            messages = capture_images(camera, wide_camera, views, messages, display_seconds=3)
            response, messages = chat_completion_request(messages=messages, client=client, model=GPT_MODEL)
            messages = perform_action(hello_robot=hello_robot, response=response, messages=messages)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()