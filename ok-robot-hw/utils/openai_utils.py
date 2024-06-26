import cv2
import base64
import json
import numpy as np
import matplotlib.pyplot as plt
from tenacity import retry, wait_random_exponential, stop_after_attempt
from utils.messages_utils import add_response_message, add_image_message, add_tool_message

# # Function to capture an image and encode it to base64
# def capture_and_encode_image(camera, messages, display_seconds=1):
#     rgb_image, _, _ = camera.capture_image()

#     # Rotate the image 90 degrees to the right
#     rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)

#     # Display the captured image
#     fig = plt.figure(figsize=(10, 10))
#     plt.imshow(rgb_image)
#     plt.title("Captured Image")
#     plt.axis('off')
#     plt.show(block=True)
#     plt.pause(display_seconds)
#     plt.close(fig)

#     _, buffer = cv2.imencode('.png', rgb_image)

#     # if buffer.nbytes > 20 * 1024 * 1024:
#     #     print("Image size exceeds 20 MB after encoding.")
    
#     encoded_image = base64.b64encode(buffer).decode('utf-8')
#     messages = add_image_message(encoded_image, messages)
#     return messages

# def capture_and_encode_image(camera, messages, display_seconds=1):
#     # Capture both RGB and depth images
#     rgb_image, depth_image, _ = camera.capture_image()

#     # Rotate both images 90 degrees to the right
#     rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
#     depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)
    
#     # Display RGB image in a separate figure
#     plt.figure(figsize=(5, 5))
#     plt.imshow(rgb_image)
#     plt.title("RGB Image")
#     plt.axis('off')
#     plt.show(block=False)
#     plt.pause(display_seconds)
#     plt.close()

#     # Display depth image in a separate figure
#     plt.figure(figsize=(5, 5))
#     depth_display = np.uint8(depth_image)
#     depth_colormap = plt.imshow(depth_display, cmap='jet')
#     plt.colorbar(depth_colormap, orientation='vertical', label='Depth Scale')
#     plt.title("Depth Image")
#     plt.axis('off')
#     plt.show(block=True)
#     plt.pause(display_seconds)
#     plt.close()

#     # Encode the RGB image
#     _, buffer = cv2.imencode('.png', rgb_image)
#     encoded_image = base64.b64encode(buffer).decode('utf-8')
#     messages = add_image_message(encoded_image=encoded_image, messages=messages, RGB=True)

#     # Encode the depth image
#     _, depth_buffer = cv2.imencode('.png', depth_image)
#     encoded_depth_image = base64.b64encode(depth_buffer).decode('utf-8')
#     messages = add_image_message(encoded_image=encoded_depth_image, messages=messages, RGB=False)

#     return messages

def capture_and_encode_image(camera, messages, display_seconds=1):
    # Capture both RGB and depth images
    rgb_image, depth_image, _ = camera.capture_image()

    # Rotate both images 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)

    # Extract the range of depth values
    min_val, max_val = depth_image.min(), depth_image.max()

    depth_image_normalized = cv2.normalize(depth_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Display RGB image in a separate figure
    plt.figure(figsize=(5, 5))
    plt.imshow(rgb_image)
    plt.title("RGB Image")
    plt.axis('off')
    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close()

    # Display depth image in a separate figure with jet colormap
    plt.figure(figsize=(5, 5))
    depth_colormap = plt.imshow(depth_image_normalized, cmap='jet')
    colorbar = plt.colorbar(depth_colormap, orientation='vertical')
    colorbar.set_label('Depth Scale')
    colorbar.set_ticks([0, 255])  # Assuming you want to show the scale of the normalized image
    colorbar.set_ticklabels([f"{min_val:.2f}m", f"{max_val:.2f}m"])  # Adjust format as needed
    plt.title("Depth Image")
    plt.axis('off')
    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close()

    # Encode the RGB image
    _, buffer = cv2.imencode('.png', rgb_image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    messages = add_image_message(encoded_image=encoded_image, messages=messages, RGB=True)

    # Apply colormap to depth image and convert to BGR for encoding
    depth_color = cv2.applyColorMap(depth_image_normalized, cv2.COLORMAP_JET)
    _, depth_buffer = cv2.imencode('.png', depth_color)
    encoded_depth_image = base64.b64encode(depth_buffer).decode('utf-8')
    messages = add_image_message(encoded_image=encoded_depth_image, messages=messages, RGB=False)

    return messages

tools = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Navigates the robot to a relative position and orientation, based on where it currently is.",
            "parallel_tool_calls": "false",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "The relative x coordinate in meters. Positive is forward."},
                    "y": {"type": "number", "description": "The relative y coordinate in meters. Positive is left"},
                    "theta": {"type": "number", "description": "The relative orientation angle in radians. Positive is counterclockwise"}
                },
                "required": ["x", "y", "theta"]
            },
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "stop",
    #         "description": "Exits the program.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {}
    #         }
    #     }
    # },
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
        messages = add_response_message(response=response, messages=messages)
        return response, messages
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return None, messages

def perform_action(hello_robot, response, messages):
    tool_calls = getattr(response.choices[0].message, 'tool_calls', None)

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
                messages = add_tool_message(tool_call, function_name, messages)
        return messages
    else:
        print("No tool call.")
        return messages

def navigate_to(robot, xyt_goal):
    print(f"Navigating robot to relative position: x={xyt_goal[0]}, y={xyt_goal[1]}, theta={xyt_goal[2]}\n")
    robot.robot.nav.navigate_to(xyt_goal, relative=True)

# def perform_action(hello_robot, response, messages):
#     tool_calls = response.choices[0].message.tool_calls

#     if tool_calls:
#         print("Tool call detected.")
#         available_functions = {
#             "navigate_to": navigate_to,
#             "stop": stop,
#         }
#         for tool_call in tool_calls:
#             function_name = tool_call.function.name
#             if function_name in available_functions:
#                 function = available_functions[function_name]
#                 if function_name == "navigate_to":
#                     function_args = json.loads(tool_call.function.arguments)
#                     xyt_goal = [function_args["x"], function_args["y"], function_args["theta"]]
#                     function(hello_robot, xyt_goal)
#                     messages = add_tool_message(tool_call, function_name, messages)
#                 else:
#                     messages = add_tool_message(tool_call, function_name, messages)
#                     function()
#         return messages
#     else:
#         print("No tool call.")
#         return messages

# # function not used atm.
# def stop():
#     print("Stopping.")
#     exit()
#     # os._exit(0)