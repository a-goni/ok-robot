import os
import signal
from wide_camera import WideCamera
from utils.asier_utils import signal_handler
from utils.openai_utils import chat_completion_request, perform_action, capture_RGB, capture_RGB_depth, capture_RGB_topdown, capture_RGB_depth_topdown, capture_RGB_depth_topdown_gripper, capture_RGB_topdown_gripper, capture_RGB_map
from utils.messages_utils import add_system_message
from openai import OpenAI
from robot import HelloRobot
from camera import RealSenseCamera

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
            # choose which version to test:
            # messages = capture_RGB(camera, messages, display_seconds=3)
            # messages = capture_RGB_depth(camera, messages, display_seconds=3)
            # messages = capture_RGB_topdown(camera, wide_camera, messages, display_seconds=3)
            # messages = capture_RGB_depth_topdown(camera, wide_camera, messages, display_seconds=3)
            # messages = capture_RGB_depth_topdown_gripper(camera, wide_camera, messages, display_seconds=3)
            # messages = capture_RGB_topdown_gripper(camera, wide_camera, messages, display_seconds=3)
            messages = capture_RGB_map(camera, messages, display_seconds=3)

            response, messages = chat_completion_request(messages=messages, client=client, model=GPT_MODEL)
            messages = perform_action(hello_robot=hello_robot, response=response, messages=messages)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()