import sys
import cv2
import base64
import json
import matplotlib.pyplot as plt
from io import BytesIO
from tenacity import retry, wait_random_exponential, stop_after_attempt
from utils.messages_utils import add_response_message, add_image_messages, add_image_message, add_tool_message

RGB_message = """
        This image displays a forward-facing RGB view with an image FOV (HxW) of 69°x42°. This is a narrow FOV, so if something appears close in your FOV, try to avoid it. The robot base is wide, so it is easy to hit things. Find the toy kitchen."""

RGB_depth_message = """
        This set includes two images: a forward-facing RGB image and a corresponding depth image. The RGB image shows the environment in color, while the depth image provides distance measurements using a color scale, which helps in understanding the spatial arrangement and distances of objects in the scene. Both these cameras have a narrow FOV, so if something appears close, avoid it by turning. The robot base is wide, so it is easy to hit things."""

RGB_topdown_message = """
        This message contains two images: the first is a forward-facing RGB image capturing what lies directly in front of the robot, and the second is a top-down view showing a fish-eyed view of the robot's surroundings from above. The forward facing camera should be used as the primary camera for for basic visual tasks and determine what is directly infront of the robot. The topdown view should be used to help avoid obstacels that are nearby and provide a fish-eyed view of the surroundings, helpful for navigation and spatial orientation."""

RGB_depth_topdown_message = """
        This message includes three images: a forward-facing RGB image, a depth image with a meter scale, and a top-down fish-eyed view from the robot. The RGB and depth images provide a detailed understanding of the space in front of the robot, while the top-down image offers a fish-eyed view of the surrounding area of the robot, helpful navigation and obstacle avoidance."""

RGB_topdown_gripper_message = """
        This message includes three images: a forward-facing RGB image, a down-facing fish-eyed view from the top of the robot, and a forward-facing fish-eyed view from the gripper. The forward facing RGB image shows what is directly infront, useful for basic visual tasks. The down-facing image offers a fish-eyed view of the surrounding area of the robot, helpful navigation and obstacle avoidance. The gripper front-facing fish-eyed view allows for a wider view facing forward, to see more of what is around in front."""

RGB_depth_topdown_gripper_message = """
        This message includes four images: a forward-facing RGB image, a depth image with a meter scale, a top-down fish-eyed view from the robot, and a forward facing fish-eyed view from the gripper. The RGB and depth images provide an understanding of the space directly in front of the robot, while the top-down image offers a fish-eyed view of the surrounding area of the robot, helpful navigation and obstacle avoidance, and the gripper front facing fish-eyed view allows for a wider view facing forward, to see more of what is around in front."""

def capture_RGB(camera, messages, display_seconds=3):
    # function encodes RGB image and adds this to the message array.
    rgb_image, _, _ = camera.capture_image()

    # Rotate the image 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)

    # Display the captured image
    fig = plt.figure(figsize=(5, 5))
    fig.canvas.manager.window.move(0,0)
    plt.imshow(rgb_image)
    plt.title("Captured Image")
    plt.axis('off')
    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close(fig)

    _, buffer = cv2.imencode('.png', rgb_image)

    encoded_images = [base64.b64encode(buffer).decode('utf-8')]
    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_message)

    return messages

def capture_RGB_depth(camera, messages, display_seconds=2):
    # Capture both RGB and depth images
    rgb_image, depth_image, _ = camera.capture_image()

    # Rotate both images 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)

    # Encode the RGB image
    _, rgb_buffer = cv2.imencode('.png', rgb_image)
    encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

    # encode the depth image with a color map
    fig = plt.figure(figsize=(5, 5))
    plt.imshow(depth_image, cmap='jet')
    plt.colorbar(orientation='vertical').set_label('Depth Scale (m)')
    plt.title("Depth Image")
    plt.axis('off')

    # Save the figure to a BytesIO object for encoding
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)  # Close the plot to free up resources
    buf.seek(0)

    # Encode the depth image
    encoded_depth_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    encoded_images = [encoded_rgb_image, encoded_depth_image]
    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_depth_message)

    # Display both images in a subplot with the color bar for the depth image
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    fig.canvas.manager.window.move(0,0)
    ax[0].imshow(rgb_image)  # Convert BGR to RGB for display
    ax[0].set_title("RGB Image")
    ax[0].axis('off')
    depth_display = ax[1].imshow(depth_image, cmap='jet')
    plt.colorbar(depth_display, ax=ax[1], orientation='vertical').set_label('Depth Scale (m)')
    ax[1].set_title("Depth Image")
    ax[1].axis('off')
    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close()

    return messages

def capture_RGB_topdown(camera, wide_camera, messages, display_seconds=2):
    # Capture RGB, depth, and wide-angle images
    rgb_image, _, _ = camera.capture_image()
    topdown_image, _ = wide_camera.capture_image()

    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB)

    # Encode the RGB image
    _, rgb_buffer = cv2.imencode('.png', rgb_image)
    encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

    # Encode the top-down image
    _, wide_buffer = cv2.imencode('.png', topdown_image)
    encoded_wide_image = base64.b64encode(wide_buffer).decode('utf-8')

    # Store encoded images
    encoded_images = [encoded_rgb_image, encoded_wide_image]

    # Display both images in a subplot
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    fig.canvas.manager.window.move(0,0)
    ax[0].imshow(rgb_image)  # Convert BGR to RGB for display
    ax[0].set_title("Forward RGB Image")
    ax[0].axis('off')

    ax[1].imshow(topdown_image)  # Convert BGR to RGB for display
    ax[1].set_title("Top-down View")
    ax[1].axis('off')

    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close()

    # Assuming add_image_messages function can handle an array of encoded images
    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_topdown_message)

    return messages

def capture_RGB_depth_topdown(camera, wide_camera, messages, display_seconds=2):
    # Capture RGB, depth, and wide-angle images
    rgb_image, depth_image, _ = camera.capture_image()
    topdown_image, _ = wide_camera.capture_image()

    # Rotate all images 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)
    topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB)

    # Encode the RGB image
    _, rgb_buffer = cv2.imencode('.png', rgb_image)
    encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

    # Encode the depth image with a colormap
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(depth_image, cmap='jet')
    plt.colorbar(ax.imshow(depth_image, cmap='jet'), orientation='vertical').set_label('Depth Scale (m)')
    ax.axis('off')
    plt.title("Forward Depth Image")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    encoded_depth_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Encode the top-down image
    _, topdown_buffer = cv2.imencode('.png', topdown_image)
    encoded_topdown_image = base64.b64encode(topdown_buffer).decode('utf-8')

    # Store encoded images
    encoded_images = [encoded_rgb_image, encoded_depth_image, encoded_topdown_image]

    # Display all images in a subplot
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    fig.canvas.manager.window.move(0,0)
    ax[0].imshow(cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB))  # Convert BGR to RGB for display
    ax[0].set_title("Forward RGB Image")
    ax[0].axis('off')

    ax[1].imshow(cv2.cvtColor(depth_image, cv2.COLOR_BGR2RGB), cmap='jet')
    colorbar = plt.colorbar(ax[1].imshow(depth_image, cmap='jet'), ax=ax[1], orientation='vertical')
    colorbar.set_label('Depth Scale (m)')
    ax[1].set_title("Forward Depth Image")
    ax[1].axis('off')

    ax[2].imshow(cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB))  # Convert BGR to RGB for display
    ax[2].set_title("Top-down View")
    ax[2].axis('off')

    plt.show(block=False)
    plt.pause(display_seconds)
    plt.close()

    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_depth_topdown_message)

    return messages

def capture_RGB_depth_topdown_gripper(camera, wide_camera, messages, display_seconds=2):
    # Capture RGB, depth, wide-angle images
    rgb_image, depth_image, _ = camera.capture_image()
    topdown_image, gripper_image = wide_camera.capture_image()

    # Rotate all images 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)
    topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB)
    gripper_image = cv2.cvtColor(gripper_image, cv2.COLOR_BGR2RGB)

    # Encode the RGB image
    _, rgb_buffer = cv2.imencode('.png', rgb_image)
    encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

    # Encode the depth image with a colormap
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(depth_image, cmap='jet')
    plt.colorbar(ax.imshow(depth_image, cmap='jet'), orientation='vertical').set_label('Depth Scale (m)')
    ax.axis('off')
    plt.title("Forward Depth Image")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    encoded_depth_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Encode the top-down image
    _, topdown_buffer = cv2.imencode('.png', topdown_image)
    encoded_topdown_image = base64.b64encode(topdown_buffer).decode('utf-8')

    # Encode the gripper image
    _, gripper_buffer = cv2.imencode('.png', gripper_image)
    encoded_gripper_image = base64.b64encode(gripper_buffer).decode('utf-8')

    # Store encoded images
    encoded_images = [encoded_rgb_image, encoded_depth_image, encoded_topdown_image, encoded_gripper_image]

    # Display all images in a subplot
    fig, ax = plt.subplots(1, 4, figsize=(15, 5))
    fig.canvas.manager.window.move(0,0)
    ax[0].imshow(rgb_image)
    ax[0].set_title("Forward RGB Image")
    ax[0].axis('off')

    ax[1].imshow(depth_image, cmap='jet')
    colorbar = plt.colorbar(ax[1].imshow(depth_image, cmap='jet'), ax=ax[1], orientation='vertical', fraction=0.06, pad=0.04)
    colorbar.set_label('Depth Scale (m)')
    ax[1].set_title("Forward Depth Image")
    ax[1].axis('off')

    ax[2].imshow(topdown_image)
    ax[2].set_title("Top-down View")
    ax[2].axis('off')

    ax[3].imshow(gripper_image)
    ax[3].set_title("Gripper View")
    ax[3].axis('off')

    plt.show(block=True)
    plt.pause(display_seconds)
    plt.close()

    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_depth_topdown_gripper_message)

    return messages

def capture_RGB_topdown_gripper(camera, wide_camera, messages, display_seconds=2):
    # Capture RGB, depth, wide-angle images
    rgb_image, _ , _ = camera.capture_image()
    topdown_image, gripper_image = wide_camera.capture_image()

    # Rotate all images 90 degrees to the right
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)
    topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_BGR2RGB)
    gripper_image = cv2.cvtColor(gripper_image, cv2.COLOR_BGR2RGB)

    # Display all images in a subplot
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    fig.canvas.manager.window.move(0,0)
    ax[0].imshow(rgb_image)
    ax[0].set_title("Forward RGB Image")
    ax[0].axis('off')

    ax[1].imshow(topdown_image)
    ax[1].set_title("Top-down View")
    ax[1].axis('off')

    ax[2].imshow(gripper_image)
    ax[2].set_title("Gripper View")
    ax[2].axis('off')

    plt.show(block=True)
    plt.pause(display_seconds)
    plt.close()

    # convert colours to BGR
    rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
    topdown_image = cv2.cvtColor(topdown_image, cv2.COLOR_RGB2BGR)
    gripper_image = cv2.cvtColor(gripper_image, cv2.COLOR_RGB2BGR)

    # Encode the RGB image
    _, rgb_buffer = cv2.imencode('.png', rgb_image)
    encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

    # Encode the top-down image
    _, topdown_buffer = cv2.imencode('.png', topdown_image)
    encoded_topdown_image = base64.b64encode(topdown_buffer).decode('utf-8')

    # Encode the gripper image
    _, gripper_buffer = cv2.imencode('.png', gripper_image)
    encoded_gripper_image = base64.b64encode(gripper_buffer).decode('utf-8')

    # Store encoded images
    encoded_images = [encoded_rgb_image, encoded_topdown_image, encoded_gripper_image]

    messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_topdown_gripper_message)

    return messages

import rospy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
import numpy as np
import cv2
import tf

RGB_map_message = """
        This message includes two images: a forward-facing RGB image with a FOV (HxW) of 69°x42° and a map image created by the onboard lidar with the robot's current pose, and travelled path. The RGB image shows what lies directly in front of the robot. The map image provides spatial context, showing the robot's location, pose, and a 1.5m circle around the robot, to help show collision areas, navigable paths, and potential areas to explore."""

# Global variables to store map and pose data
map_data = None
robot_pose = None
past_positions = []

def capture_RGB_map(camera, messages, display_seconds=2):
    global map_data, robot_pose, past_positions

    # Capture the RGB image
    rgb_image, _, _ = camera.capture_image()
    rgb_image = cv2.rotate(rgb_image, cv2.ROTATE_90_CLOCKWISE)

    # Callback functions to update map and pose data
    def map_callback(map_msg):
        global map_data
        map_data = map_msg

    def slam_out_pose_callback(pose_msg):
        global robot_pose
        position = pose_msg.pose.position
        orientation = pose_msg.pose.orientation
        euler = tf.transformations.euler_from_quaternion([orientation.x, orientation.y, orientation.z, orientation.w])
        robot_pose = (position.x, position.y, euler[2])

    # Subscribe to the map and pose topics
    map_sub = rospy.Subscriber('/map', OccupancyGrid, map_callback)
    pose_sub = rospy.Subscriber('/slam_out_pose', PoseStamped, slam_out_pose_callback)

    # Allow some time to receive messages
    rospy.sleep(1)

    # Process the map data to create an image
    if map_data and robot_pose:
        width = map_data.info.width
        height = map_data.info.height
        resolution = map_data.info.resolution
        origin_x = map_data.info.origin.position.x
        origin_y = map_data.info.origin.position.y
        data = np.array(map_data.data).reshape((height, width))

        # Convert the map data to an image
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[data == 100] = [0, 0, 0]         # Occupied cells are black
        img[data == -1] = [128, 128, 128]    # Unknown cells are gray
        img[data == 0] = [255, 255, 255]     # Free cells are white

        # Find the bounding box of occupied and free cells
        mask = (data == 100) | (data == 0)
        coords = np.argwhere(mask)
        if coords.size > 0:
            top_left = coords.min(axis=0)
            bottom_right = coords.max(axis=0)
            img_cropped = img[top_left[0]:bottom_right[0]+1, top_left[1]:bottom_right[1]+1]
        else:
            img_cropped = img  # If no occupied or free cells, keep the original image

        # Add robot pose to the image
        robot_x, robot_y, robot_theta = robot_pose
        map_x = int((robot_x - origin_x) / resolution)
        map_y = int((robot_y - origin_y) / resolution)

        # Convert to coordinates relative to the cropped image
        map_x -= top_left[1]
        map_y -= top_left[0]

        # Draw the robot's past positions as a faint line
        if len(past_positions) > 1:
            for i in range(1, len(past_positions)):
                cv2.line(img_cropped,
                         (int((past_positions[i-1][0] - origin_x) / resolution) - top_left[1],
                          int((past_positions[i-1][1] - origin_y) / resolution) - top_left[0]),
                         (int((past_positions[i][0] - origin_x) / resolution) - top_left[1],
                          int((past_positions[i][1] - origin_y) / resolution) - top_left[0]),
                         (255, 0, 0), 1)

        # Draw a 1.5m radius circle around the robot's position
        radius = int(1.5 / resolution)  # Convert 1.5 meters to pixels
        cv2.circle(img_cropped, (map_x, map_y), radius, (0, 255, 0), 1)

        # Draw robot position (a circle) and orientation (a line)
        cv2.circle(img_cropped, (map_x, map_y), 2, (0, 0, 255), -1)
        line_length = 10
        line_x = int(map_x + line_length * np.cos(robot_theta))
        line_y = int(map_y + line_length * np.sin(robot_theta))
        cv2.line(img_cropped, (map_x, map_y), (line_x, line_y), (0, 0, 255), 2)

        # Append the current robot position to the past positions
        past_positions.append((robot_x, robot_y))

        image_to_show = img_cropped
        image_to_show = cv2.flip(image_to_show, 1)
        # image_to_show = cv2.flip(image_to_show, 0)

        # Display the captured images
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        fig.canvas.manager.window.move(0, 0)
        ax[0].imshow(rgb_image)
        ax[0].set_title("Captured RGB Image")
        ax[0].axis('off')

        ax[1].imshow(image_to_show)
        ax[1].set_title("Map with Robot Pose")
        ax[1].axis('off')

        plt.show(block=True)
        plt.pause(display_seconds)
        plt.close(fig)

        # Encode the images
        _, rgb_buffer = cv2.imencode('.png', rgb_image)
        encoded_rgb_image = base64.b64encode(rgb_buffer).decode('utf-8')

        _, map_buffer = cv2.imencode('.png', image_to_show)
        encoded_map_image = base64.b64encode(map_buffer).decode('utf-8')
        encoded_images = [encoded_rgb_image, encoded_map_image]

        messages = add_image_messages(encoded_images=encoded_images, messages=messages, message=RGB_map_message)
    else:
        messages = add_image_message(encoded_images=[base64.b64encode(cv2.imencode('.png', rgb_image)[1]).decode('utf-8')], messages=messages, message="Could not capture map data.")

    # Unsubscribe from the topics
    map_sub.unregister()
    pose_sub.unregister()

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
    