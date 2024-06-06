import numpy as np

def compute_tilt(camera_xyz, target_xyz):
    vector = camera_xyz - target_xyz
    return -np.arctan2(vector[2], np.linalg.norm(vector[:2]))

def read_input():
    A = str(input("Enter A: "))
    print("A = ", A)
    B = str(input("Enter B: "))
    print("B = ", B)
    return A, B
