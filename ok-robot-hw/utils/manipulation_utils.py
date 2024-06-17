import time
from utils.grasper_utils import pickup, move_to_point, capture_and_process_image
from utils.asier_utils import get_yes_or_no
from camera import RealSenseCamera
from global_parameters import *

def run_manipulation(hello_robot, socket, text, transform_node, base_node):
    gripper_pos = 1
    hello_robot.move_to_position(arm_pos=INIT_ARM_POS,
                                 head_pan=INIT_HEAD_PAN,
                                 head_tilt=INIT_HEAD_TILT,
                                 gripper_pos=gripper_pos)
    time.sleep(1)
    hello_robot.move_to_position(lift_pos=INIT_LIFT_POS,
                                 wrist_pitch=INIT_WRIST_PITCH,
                                 wrist_roll=INIT_WRIST_ROLL,
                                 wrist_yaw=INIT_WRIST_YAW)
    time.sleep(2)
    camera = RealSenseCamera(hello_robot.robot)
    rotation, translation, depth = capture_and_process_image(
        camera=camera,
        mode='pick',
        obj=text,
        socket=socket,
        hello_robot=hello_robot)
    if rotation is None:
        return False
    if get_yes_or_no("Do you want to do this manipulation? Y or N: ") != 'N':
        pickup(hello_robot, rotation, translation, base_node, transform_node, gripper_depth=depth)
    hello_robot.move_to_position(base_trans=-hello_robot.robot.manip.get_joint_positions()[0])
    return True

def run_place(hello_robot, socket, text, transform_node, base_node):
    camera = RealSenseCamera(hello_robot.robot)
    time.sleep(2)
    rotation, translation, _ = capture_and_process_image(
        camera=camera,
        mode='place',
        obj=text,
        socket=socket,
        hello_robot=hello_robot)
    if rotation is None:
        return False
    print(rotation)
    hello_robot.move_to_position(lift_pos=1.05)
    time.sleep(1)
    hello_robot.move_to_position(wrist_yaw=0, wrist_pitch=0)
    time.sleep(2)
    move_to_point(hello_robot, translation, base_node, transform_node, move_mode=0)
    hello_robot.move_to_position(gripper_pos=1)
    hello_robot.move_to_position(lift_pos=hello_robot.robot.manip.get_joint_positions()[1] + 0.3)
    hello_robot.move_to_position(wrist_roll=3)
    time.sleep(1)
    hello_robot.move_to_position(wrist_roll=-3)
    time.sleep(4)
    hello_robot.move_to_position(gripper_pos=1,
                                 lift_pos=1.05,
                                 arm_pos=0)
    time.sleep(4)
    hello_robot.move_to_position(wrist_pitch=-1.57)
    time.sleep(1)
    hello_robot.move_to_position(base_trans=-hello_robot.robot.manip.get_joint_positions()[0])
    return True

def run_manipulation_gpt(hello_robot, socket, text, transform_node, base_node):
    gripper_pos = 1
    hello_robot.move_to_position(arm_pos=INIT_ARM_POS,
                                 head_pan=INIT_HEAD_PAN,
                                 head_tilt=INIT_HEAD_TILT,
                                 gripper_pos=gripper_pos)
    time.sleep(1)
    hello_robot.move_to_position(lift_pos=INIT_LIFT_POS,
                                 wrist_pitch=INIT_WRIST_PITCH,
                                 wrist_roll=INIT_WRIST_ROLL,
                                 wrist_yaw=INIT_WRIST_YAW)
    time.sleep(2)
    camera = RealSenseCamera(hello_robot.robot)
    rotation, translation, depth = capture_and_process_image(
        camera=camera,
        mode='pick',
        obj=text,
        socket=socket,
        hello_robot=hello_robot)
    if rotation is None:
        return False
    # removed the prompt to ask if the user wants to do the manipulation
    pickup(hello_robot, rotation, translation, base_node, transform_node, gripper_depth=depth)
    hello_robot.move_to_position(base_trans=-hello_robot.robot.manip.get_joint_positions()[0])
    return True

def run_place_gpt(hello_robot, socket, text, transform_node, base_node):
    camera = RealSenseCamera(hello_robot.robot)
    time.sleep(2)
    rotation, translation, _ = capture_and_process_image(
        camera=camera,
        mode='place',
        obj=text,
        socket=socket,
        hello_robot=hello_robot)
    if rotation is None:
        return False
    print(rotation)
    hello_robot.move_to_position(lift_pos=1.05)
    time.sleep(1)
    hello_robot.move_to_position(wrist_yaw=0, wrist_pitch=0)
    time.sleep(2)
    move_to_point(hello_robot, translation, base_node, transform_node, move_mode=0)
    hello_robot.move_to_position(gripper_pos=1)
    hello_robot.move_to_position(lift_pos=hello_robot.robot.manip.get_joint_positions()[1] + 0.3)
    hello_robot.move_to_position(wrist_roll=3)
    time.sleep(1)
    hello_robot.move_to_position(wrist_roll=-3)
    time.sleep(4)
    hello_robot.move_to_position(gripper_pos=1,
                                 lift_pos=1.05,
                                 arm_pos=0)
    time.sleep(4)
    hello_robot.move_to_position(wrist_pitch=-1.57)
    time.sleep(1)
    hello_robot.move_to_position(base_trans=-hello_robot.robot.manip.get_joint_positions()[0])
    return True
