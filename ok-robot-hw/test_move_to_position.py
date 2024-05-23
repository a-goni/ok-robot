import time

from robot import HelloRobot
from global_parameters import *

def test_move_to_position():
    # Initialize HelloRobot instance

    transform_node = GRIPPER_MID_NODE

    hello_robot = HelloRobot(end_link=transform_node)

    # Test move_to_position with example parameters
    try:
        hello_robot.move_to_position(
            arm_pos=0.5,
            head_pan=0,
            head_tilt=-1.0,
            gripper_pos=1.0
        )
        time.sleep(1)
        hello_robot.move_to_position(
            lift_pos=0.5,
            wrist_pitch=0,
            wrist_roll=0,
            wrist_yaw=0
        )
        # print("Move to position successful.")
    except Exception as e:
        print(f"Error occurred during move_to_position: {e}")


if __name__ == "__main__":
    test_move_to_position()