import time
import signal
import zmq
from robot import HelloRobot
from args import get_args2
from utils.asier_utils import get_yes_or_no, get_A_near_B_objects, get_A_object, signal_handler
from global_parameters import *
from utils.navigation_utils import load_offset, run_navigation
from utils.manipulation_utils import run_manipulation, run_place

def run():
    args = get_args2()
    load_offset(args.x1, args.y1, args.x2, args.y2)
    base_node = TOP_CAMERA_NODE
    transform_node = GRIPPER_MID_NODE
    hello_robot = HelloRobot(end_link=transform_node)
    context = zmq.Context()
    nav_socket = context.socket(zmq.REQ)
    nav_socket.connect("tcp://" + args.ipw + ":" + str(args.navigation_port))
    anygrasp_socket = context.socket(zmq.REQ)
    anygrasp_socket.connect("tcp://" + args.ipc + ":" + str(args.manipulation_port))
    while True:
        try:
            A = None
            if get_yes_or_no("You want to run navigation? Y or N: ") != "N":
                while True:
                    A, B = get_A_near_B_objects()
                    hello_robot.robot.switch_to_navigation_mode()
                    hello_robot.robot.move_to_post_nav_posture()
                    hello_robot.robot.head.look_front()
                    end_xyz = run_navigation(hello_robot.robot, nav_socket, A, B)
                    if end_xyz is not None:
                        break
                    else:
                        if get_yes_or_no("Would you like to retry the prompt? Y or N: ") == 'N':
                            break
            if get_yes_or_no("You want to run manipulation? Y or N: ") != 'N':
                while True:
                    if A is None:
                        A = get_A_object()
                    hello_robot.robot.switch_to_manipulation_mode()
                    hello_robot.robot.head.look_at_ee()
                    perform_manip = run_manipulation(hello_robot, anygrasp_socket, A, transform_node, base_node)
                    if perform_manip:
                        break
                    else:
                        if get_yes_or_no("Would you like to retry the prompt? Y or N: ") == 'N':
                            break
            A, B = None, None
            if get_yes_or_no("You want to run navigation? Y or N: ") != "N":
                while True:
                    A, B = get_A_near_B_objects()
                    hello_robot.robot.switch_to_navigation_mode()
                    hello_robot.robot.head.look_front()
                    end_xyz = run_navigation(hello_robot.robot, nav_socket, A, B)
                    if end_xyz is not None:
                        break
                    else:
                        if get_yes_or_no("Would you like to retry the prompt? Y or N: ") == 'N':
                            break
            if get_yes_or_no("You want to run place? Y or N: ") != 'N':
                while True:
                    if A is None:
                        A = get_A_object()
                    hello_robot.robot.switch_to_manipulation_mode()
                    hello_robot.robot.head.look_at_ee()
                    run_place(hello_robot, anygrasp_socket, A, transform_node, base_node)
                    if perform_manip:
                        break
                    else:
                        if get_yes_or_no("Would you like to retry the prompt? Y or N: ") == 'N':
                            break
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()