import os
import signal
from utils.asier_utils import signal_handler
from utils.openai_utils import capture_and_encode_image, chat_completion_request, perform_action, pretty_print_conversation
from openai import OpenAI
from robot import HelloRobot
from camera import RealSenseCamera

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o"

def run():    
    hello_robot = HelloRobot()
    camera = RealSenseCamera(hello_robot.robot)
    hello_robot.robot.switch_to_navigation_mode()
    hello_robot.robot.move_to_post_nav_posture()
    hello_robot.robot.head.look_front()
    messages = []
    messages.append({
        "role": "system",
        "content":
        """
        You are an autonomous robot in a lab environment with a mobile base and a camera.        
        Your task is to explore the environment, avoiding obstacles at all cost, to find the kitchen.
        Succinctly describe what you want to do and use the provided functions to navigate the area.
        Do not execute movements in parallel. All movements in one action.
        You must use the function:
            - navigate_to()
        """
    })
    while True:
        try:
            encoded_image = capture_and_encode_image(camera)
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Image has a FOV (HxW) of 69°x42°."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                            }   
                    }
                ]})
            response = chat_completion_request(messages=messages, client=client, model=GPT_MODEL)
            # messages.append(response.choices[0].message)
            print(response)
            # print(messages)
            # pretty_print_conversation(messages)
            perform_action(hello_robot, response)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()