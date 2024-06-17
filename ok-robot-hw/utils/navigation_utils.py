import numpy as np
from utils.communication_utils import send_array, recv_array
from utils.asier_utils import get_yes_or_no
from global_parameters import *

X_OFFSET, Y_OFFSET, THETA_OFFSET, r2n_matrix, n2r_matrix = None, None, None, None, None

def load_offset(x1, y1, x2, y2):
    global X_OFFSET, Y_OFFSET, THETA_OFFSET, r2n_matrix, n2r_matrix
    X_OFFSET = x1
    Y_OFFSET = y1
    THETA_OFFSET = np.arctan2((y2 - y1), (x2 - x1))
    print(f"offsets - {X_OFFSET}, {Y_OFFSET}, {THETA_OFFSET}")
    r2n_matrix = \
        np.array([
            [1, 0, X_OFFSET],
            [0, 1, Y_OFFSET],
            [0, 0, 1]
        ]) @ \
        np.array([
            [np.cos(THETA_OFFSET), -np.sin(THETA_OFFSET), 0],
            [np.sin(THETA_OFFSET), np.cos(THETA_OFFSET), 0],
            [0, 0, 1]
        ])
    n2r_matrix = \
        np.array([
            [np.cos(THETA_OFFSET), np.sin(THETA_OFFSET), 0],
            [-np.sin(THETA_OFFSET), np.cos(THETA_OFFSET), 0],
            [0, 0, 1]
        ]) @ \
        np.array([
            [1, 0, -X_OFFSET],
            [0, 1, -Y_OFFSET],
            [0, 0, 1]
        ])

def navigate(robot, xyt_goal):
    xyt_goal = np.asarray(xyt_goal)
    while xyt_goal[2] < -np.pi or xyt_goal[2] > np.pi:
        xyt_goal[2] = xyt_goal[2] + 2 * np.pi if xyt_goal[2] < -np.pi else xyt_goal[2] - 2 * np.pi
    while True:
        robot.nav.navigate_to(xyt_goal, blocking=False)
        xyt_curr = robot.nav.get_base_pose()
        print("The robot currently loactes at " + str(xyt_curr))
        if np.allclose(xyt_curr[:2], xyt_goal[:2], atol=POS_TOL) and \
                (np.allclose(xyt_curr[2], xyt_goal[2], atol=YAW_TOL) \
                 or np.allclose(xyt_curr[2], xyt_goal[2] + np.pi * 2, atol=YAW_TOL) \
                 or np.allclose(xyt_curr[2], xyt_goal[2] - np.pi * 2, atol=YAW_TOL)):
            print("The robot is finally at " + str(xyt_goal))
            break

def run_navigation(robot, socket, A, B):
    start_xy = robot.nav.get_base_pose()
    print(start_xy)
    transformed_start_xy = r2n_matrix @ np.array([start_xy[0], start_xy[1], 1])
    start_xy[0], start_xy[1] = transformed_start_xy[0], transformed_start_xy[1]
    start_xy[2] += THETA_OFFSET
    print(start_xy)
    send_array(socket, start_xy)
    print(socket.recv_string())
    socket.send_string(A)
    print(socket.recv_string())
    socket.send_string(B)
    print(socket.recv_string())
    socket.send_string("Waiting for path")
    paths = recv_array(socket)
    print(paths)
    socket.send_string("Path received")
    end_xyz = recv_array(socket)
    z = end_xyz[2]
    end_xyz = (n2r_matrix @ np.array([end_xyz[0], end_xyz[1], 1]))
    end_xyz[2] = z
    if get_yes_or_no("Do you want to follow this path? Y or N: ") == 'N':
        return None
    robot.nav.set_velocity(v=25, w=20)
    final_paths = []
    for path in paths:
        transformed_path = n2r_matrix @ np.array([path[0], path[1], 1])
        transformed_path[2] = path[2] - THETA_OFFSET
        print(transformed_path)
        final_paths.append(transformed_path)
        navigate(robot, transformed_path)
    xyt = robot.nav.get_base_pose()
    xyt[2] = xyt[2] + np.pi / 2
    navigate(robot, xyt)
    return end_xyz

def run_navigation_gpt(robot, socket, A, B):
    start_xy = robot.nav.get_base_pose()
    print(start_xy)
    transformed_start_xy = r2n_matrix @ np.array([start_xy[0], start_xy[1], 1])
    start_xy[0], start_xy[1] = transformed_start_xy[0], transformed_start_xy[1]
    start_xy[2] += THETA_OFFSET
    print(start_xy)
    send_array(socket, start_xy)
    print(socket.recv_string())
    socket.send_string(A)
    print(socket.recv_string())
    socket.send_string(B)
    print(socket.recv_string())
    socket.send_string("Waiting for path")
    paths = recv_array(socket)
    print(paths)
    socket.send_string("Path received")
    end_xyz = recv_array(socket)
    z = end_xyz[2]
    end_xyz = (n2r_matrix @ np.array([end_xyz[0], end_xyz[1], 1]))
    end_xyz[2] = z
    # Line removed for GPT
    # if get_yes_or_no("Do you want to follow this path? Y or N: ") == 'N':
    #     return None
    robot.nav.set_velocity(v=25, w=20)
    final_paths = []
    for path in paths:
        transformed_path = n2r_matrix @ np.array([path[0], path[1], 1])
        transformed_path[2] = path[2] - THETA_OFFSET
        print(transformed_path)
        final_paths.append(transformed_path)
        navigate(robot, transformed_path)
    xyt = robot.nav.get_base_pose()
    xyt[2] = xyt[2] + np.pi / 2
    navigate(robot, xyt)
    return end_xyz
