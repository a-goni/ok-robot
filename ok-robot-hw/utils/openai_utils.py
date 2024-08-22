import sys
import cv2
import base64
import json
import matplotlib.pyplot as plt
from io import BytesIO
from tenacity import retry, wait_random_exponential, stop_after_attempt
from utils.messages_utils import add_response_message, add_image_messages, add_tool_message

import rospy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
import numpy as np
import tf

# Messages
messages_dict = {
    'RGB': """\nRGB Image: This is a forward-facing RGB image with a FOV of 69x42 degrees (HxW). The position of the camera is on the robots head (approx. 1.4m above ground), facing slightly down. This image provides colour information of the scene in front of the robot...""",
    'Depth': """\nDepth Image: This is a forawrd-facing depth image with a FOV of 69x42 degrees (HxW). The position of the camera is on the robots head (approx. 1.4m above ground), facing slightly down. This image provides distance measurements using a color scale to help understand the spatial arrangement and distances of scene in front of the robot...""",
    'WideDown': """\nWide Down View: This is a down-facing fish-eyed image with a FOV of 185 degrees. The position of the camera is above the robots head (approx. 1.5m above ground). This image is helpful for navigation and spatial orientation. As this is a fish-eyed lens, the image is distorted, inparticular around the edges. The kitchen might be in the edge of the photo...""",
    'WideGripper': """\nForward Gripper View: This is a forward-facing fisheyed image with a FOV of 185 degrees. The position of the camera is on the robots wrist (approx 0.8m above the ground), facing forward, level with the ground. This image is helpful for viewing which objects are infront. As this is a fish-eyed lens, the image is distorted, inparticular around the edges. The kitchen might be in the edge of the photo...""",
    'Map': """\nMap: This is a map generated from the lidar scan on the robot. This image provides spatial context, showing the robot's location/pose in blue, previous path in red, and a 1.5m green circle around the robot. White signifies area with no obstacles that you can explore, black signifies a wall or an object to avoid, and grey signifies areas that we cannot see or potentially unnavigable area. Use the robots pose (blue) and the identified obstacles (black) to help avoid running into things. Keep all obstacles outside the green circle..."""
}

# Global variables to store map and pose data
map_data = None
robot_pose = None
past_positions = []

def process_depth_image(depth_image):
    fig = plt.figure(figsize=(5, 5))
    plt.imshow(depth_image, cmap='jet')
    plt.colorbar(orientation='vertical').set_label('Depth Scale (m)')
    plt.title("Depth Image")
    plt.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def process_image(image):
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')

def display_images(images, titles, display_seconds=3):
    fig, ax = plt.subplots(1, len(images), figsize=(5 * len(images), 5))
    fig.canvas.manager.window.move(0, 0)
    
    if len(images) == 1:
        ax.imshow(images[0])
        ax.set_title(titles[0])
        ax.axis('off')
    else:
        for i in range(len(images)):
            ax[i].imshow(images[i])
            ax[i].set_title(titles[i])
            ax[i].axis('off')
    
    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close(fig)

def capture_images(camera, wide_camera, views, messages, display_seconds=3):
    captured_images = []
    encoded_images = []
    titles = []

    for view in views:
        if view == 'RGB':
            rgb_image, _, _ = camera.capture_image()
            rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
            captured_images.append(rgb_image)
            rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
            encoded_images.append(process_image(rgb_image))
            titles.append("Forward RGB Image")

        elif view == 'Depth':
            _, depth_image, _ = camera.capture_image()
            depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)
            # depth_image = depth_image.astype(np.float32)
            captured_images.append(depth_image)
            depth_image = cv2.cvtColor(depth_image, cv2.COLOR_RGB2BGR)
            encoded_images.append(process_depth_image(depth_image))
            titles.append("Forward Depth Image")

        elif view == 'WideDown':
            topdown_image, _ = wide_camera.capture_image()
            topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB)
            captured_images.append(topdown_image)
            topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_RGB2BGR)
            encoded_images.append(process_image(topdown_image))
            titles.append("Top-down View")

        elif view == 'WideGripper':
            _, gripper_image = wide_camera.capture_image()
            gripper_image = cv2.cvtColor(gripper_image, cv2.COLOR_BGR2RGB)
            captured_images.append(gripper_image)
            gripper_image = cv2.cvtColor(gripper_image, cv2.COLOR_RGB2BGR)
            encoded_images.append(process_image(gripper_image))
            titles.append("Gripper View")

        elif view == 'Map':            
            # Capture and process map data
            global map_data, robot_pose, past_positions
            map_sub = rospy.Subscriber('/map', OccupancyGrid, map_callback)
            pose_sub = rospy.Subscriber('/slam_out_pose', PoseStamped, slam_out_pose_callback)
            rospy.sleep(1)
            if map_data and robot_pose:
                map_image = process_map_data(map_data, robot_pose)
                map_image = cv2.flip(map_image, 1)
                captured_images.append(map_image)
                map_image = cv2.cvtColor(map_image, cv2.COLOR_RGB2BGR)
                encoded_images.append(process_image(map_image))
                titles.append("Map with Robot Pose")
            map_sub.unregister()
            pose_sub.unregister()

    display_images(captured_images, titles, display_seconds)
    message = create_message(views)
    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=message)

    return messages

import textwrap
def create_message(views):
    message = f"This message contains {len(views)} image(s):\n"
    for view in views:
        if view in messages_dict:
            message += f"{messages_dict[view]}"
    return message.strip()

def map_callback(map_msg):
    global map_data
    map_data = map_msg

def slam_out_pose_callback(pose_msg):
    global robot_pose
    position = pose_msg.pose.position
    orientation = pose_msg.pose.orientation
    euler = tf.transformations.euler_from_quaternion([orientation.x, orientation.y, orientation.z, orientation.w])
    robot_pose = (position.x, position.y, euler[2])

def process_map_data(map_data, robot_pose):
    global past_positions
    width = map_data.info.width
    height = map_data.info.height
    resolution = map_data.info.resolution
    origin_x = map_data.info.origin.position.x
    origin_y = map_data.info.origin.position.y
    data = np.array(map_data.data).reshape((height, width))

    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[data == 100] = [0, 0, 0]         # Occupied cells are black
    img[data == -1] = [128, 128, 128]    # Unknown cells are gray
    img[data == 0] = [255, 255, 255]     # Free cells are white

    mask = (data == 100) | (data == 0)
    coords = np.argwhere(mask)
    if coords.size > 0:
        top_left = coords.min(axis=0)
        bottom_right = coords.max(axis=0)
        img_cropped = img[top_left[0]:bottom_right[0]+1, top_left[1]:bottom_right[1]+1]
    else:
        img_cropped = img

    robot_x, robot_y, robot_theta = robot_pose
    map_x = int((robot_x - origin_x) / resolution)
    map_y = int((robot_y - origin_y) / resolution)
    map_x -= top_left[1]
    map_y -= top_left[0]

    past_positions.append((robot_x, robot_y))

    if len(past_positions) > 1:
        for i in range(1, len(past_positions)):
            cv2.line(img_cropped,
                     (int((past_positions[i-1][0] - origin_x) / resolution) - top_left[1],
                      int((past_positions[i-1][1] - origin_y) / resolution) - top_left[0]),
                     (int((past_positions[i][0] - origin_x) / resolution) - top_left[1],
                      int((past_positions[i][1] - origin_y) / resolution) - top_left[0]),
                     (255, 0, 0), 1)

    radius = int(1.5 / resolution)
    cv2.circle(img_cropped, (map_x, map_y), radius, (0, 255, 0), 1)
    cv2.circle(img_cropped, (map_x, map_y), 7, (0, 0, 255), -1)
    line_length = 15
    line_x = int(map_x + line_length * np.cos(robot_theta))
    line_y = int(map_y + line_length * np.sin(robot_theta))
    cv2.line(img_cropped, (map_x, map_y), (line_x, line_y), (0, 0, 255), 2)

    # past_positions.append((robot_x, robot_y))

    return img_cropped


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
                    "theta": {"type": "number", "description": "The relative orientation angle in radians. Positive is counterclockwise (left)"}
                },
                "required": ["x", "y", "theta"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop",
            "description": "Exits the program. Only used to end all further actions.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
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
            "stop": stop  # Add the stop function here
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name in available_functions:
                function = available_functions[function_name]
                if function_name == "navigate_to":
                    function_args = json.loads(tool_call.function.arguments)
                    xyt_goal = [function_args["x"], function_args["y"], function_args["theta"]]
                    function(hello_robot, xyt_goal)
                elif function_name == "stop":
                    function()  # Call the stop function without arguments
                messages = add_tool_message(tool_call, function_name, messages)
        return messages
    else:
        print("No tool call.")
        return messages

def navigate_to(robot, xyt_goal):
    print(f"Navigating robot to relative position: x={xyt_goal[0]}, y={xyt_goal[1]}, theta={xyt_goal[2]}\n")
    robot.robot.nav.navigate_to(xyt_goal, relative=True)

# function not used atm.
def stop():
    print("Stopping.")
    sys.exit(0)
    