# this code literally just gets the robot to move xm on every loop
# x is forward, y is horizontal, and t is direction, all is relative to original position

import signal
from utils.asier_utils import signal_handler
from robot import HelloRobot

def run():    
    hello_robot = HelloRobot()
    hello_robot.robot.switch_to_navigation_mode()
    hello_robot.robot.move_to_post_nav_posture() # check if this is needed
    hello_robot.robot.head.look_front()
    loop = 0
    while True:
        loop=loop + 1
        print(loop)
        try:
            xyt_goal=[0,0,1]
            hello_robot.robot.nav.navigate_to(xyt_goal, relative=True)
            break

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            break


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    run()