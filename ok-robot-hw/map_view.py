#!/usr/bin/env python

import rospy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
import numpy as np
import cv2
import tf

image_to_show = None
robot_pose = None

def map_callback(map_msg):
    global image_to_show, robot_pose
    width = map_msg.info.width
    height = map_msg.info.height
    resolution = map_msg.info.resolution
    origin_x = map_msg.info.origin.position.x
    origin_y = map_msg.info.origin.position.y
    data = np.array(map_msg.data).reshape((height, width))

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
    if robot_pose is not None:
        # Convert pose to map coordinates
        robot_x, robot_y, robot_theta = robot_pose
        map_x = int((robot_x - origin_x) / resolution)
        map_y = int((robot_y - origin_y) / resolution)

        # Convert to coordinates relative to the cropped image
        map_x -= top_left[1]
        map_y -= top_left[0]

        # Draw robot position (a circle) and orientation (a line)
        cv2.circle(img_cropped, (map_x, map_y), 5, (0, 0, 255), -1)
        line_length = 10
        line_x = int(map_x + line_length * np.cos(robot_theta))
        line_y = int(map_y - line_length * np.sin(robot_theta))  # y is inverted in image coordinates
        cv2.line(img_cropped, (map_x, map_y), (line_x, line_y), (0, 0, 255), 2)

    image_to_show = img_cropped

def slam_out_pose_callback(pose_msg):
    global robot_pose
    position = pose_msg.pose.position
    orientation = pose_msg.pose.orientation
    euler = tf.transformations.euler_from_quaternion([orientation.x, orientation.y, orientation.z, orientation.w])
    robot_pose = (position.x, position.y, euler[2])

def main():
    global image_to_show
    rospy.init_node('map_to_image', anonymous=True)
    rospy.Subscriber('/map', OccupancyGrid, map_callback)
    rospy.Subscriber('/slam_out_pose', PoseStamped, slam_out_pose_callback)

    # Main loop to display the image
    while not rospy.is_shutdown():
        if image_to_show is not None:
            cv2.imshow("Cropped Map with Robot Pose", image_to_show)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()