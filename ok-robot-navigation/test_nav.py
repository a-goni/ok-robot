import sys
import os
import torch
import numpy as np
from omegaconf import OmegaConf
import hydra
import argparse

# Adjust the system path to include the directory containing voxel_map_localizer and other modules
sys.path.append(os.path.join(os.path.dirname(__file__), "voxel_map"))
sys.path.append(os.path.join(os.path.dirname(__file__), "a_star"))

from voxel_map_localizer import VoxelMapLocalizer
from path_planner import PathPlanner
from visualizations import visualize_path  # Ensure correct import

X_OFFSET, Y_OFFSET, THETA_OFFSET, r2n_matrix, n2r_matrix = None, None, None, None, None

def load_offset(x1, y1, x2, y2):
    global X_OFFSET, Y_OFFSET, THETA_OFFSET, r2n_matrix, n2r_matrix
    X_OFFSET = x1
    Y_OFFSET = y1
    THETA_OFFSET = np.arctan2((y2 - y1), (x2 - x1))

    r2n_matrix = (
        np.array([
            [1, 0, X_OFFSET],
            [0, 1, Y_OFFSET],
            [0, 0, 1]
        ]) @ 
        np.array([
            [np.cos(THETA_OFFSET), -np.sin(THETA_OFFSET), 0],
            [np.sin(THETA_OFFSET), np.cos(THETA_OFFSET), 0],
            [0, 0, 1]
        ])
    )

    n2r_matrix = (
        np.array([
            [np.cos(THETA_OFFSET), np.sin(THETA_OFFSET), 0],
            [-np.sin(THETA_OFFSET), np.cos(THETA_OFFSET), 0],
            [0, 0, 1]
        ]) @ 
        np.array([
            [1, 0, -X_OFFSET],
            [0, 1, -Y_OFFSET],
            [0, 0, 1]
        ])
    )

def load_dataset(cfg):
    if os.path.exists(cfg.cache_path):
        return torch.load(cfg.cache_path)
    r3d_dataset = R3DSemanticDataset(cfg.dataset_path, cfg.custom_labels, subsample_freq=cfg.sample_freq)
    semantic_memory = OWLViTLabelledDataset(
        r3d_dataset,
        owl_model_name=cfg.web_models.owl,
        sam_model_type=cfg.web_models.sam,
        device=cfg.memory_load_device,
        threshold=cfg.threshold,
        subsample_prob=cfg.subsample_prob,
        visualize_results=cfg.visualize_results,
        visualization_path=cfg.visualization_path,
    )
    torch.save(semantic_memory, cfg.cache_path)
    return semantic_memory

def get_best_paths(planner, localizer, start_xyt, A, B, num_paths=3, cfg=None):
    paths = []
    for _ in range(num_paths):
        end_xyz = localizer.localize_AonB(A, B)
        end_xy = end_xyz[:2]
        path = planner.plan(start_xy=start_xyt[:2], end_xy=end_xy, remove_line_of_sight_points=True)
        paths.append((path, end_xyz))
        
        # Visualize path unconditionally
        print("Visualizing path...")  # Debug print
        visualize_path(path, end_xyz, cfg)
        
    return paths

@hydra.main(version_base=None, config_path="configs", config_name="path")
def main(cfg):
    # Parse additional command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--x1", type=float, required=True, help="X coordinate of the starting position")
    parser.add_argument("--y1", type=float, required=True, help="Y coordinate of the starting position")
    parser.add_argument("--x2", type=float, required=True, help="X coordinate of the second position")
    parser.add_argument("--y2", type=float, required=True, help="Y coordinate of the second position")
    args = parser.parse_args()

    cfg.max_height = cfg.min_height + 1.5  # Calculate and set max_height
    semantic_memory = load_dataset(cfg)

    load_offset(args.x1, args.y1, args.x2, args.y2)

    planner = PathPlanner(
        cfg.dataset_path,
        cfg.min_height,
        cfg.max_height,
        cfg.resolution,
        cfg.occ_avoid_radius,
        cfg.map_type == "conservative_vlmap",
    )
    localizer = VoxelMapLocalizer(
        semantic_memory,
        owl_vit_config=cfg.web_models.owl,
        device=cfg.path_planning_device,
    )

    # Compute the start_xy based on the provided starting position
    start_xyt = np.array([args.x1, args.y1, THETA_OFFSET])  # Adjusted for initial starting position

    while True:
        A = input("Enter A: ")
        B = input("Enter B (optional): ") or None

        paths = get_best_paths(planner, localizer, start_xyt, A, B, cfg=cfg)
        
        for i, (path, end_xyz) in enumerate(paths):
            print(f"Path option {i + 1}:")
            print(path)
            accept = input("Do you accept this path? (y/n): ").lower()
            if accept == 'y':
                print("Path accepted.")
                break
            elif i == len(paths) - 1:
                print("No more path options available.")
            else:
                print("Showing next best path...")

if __name__ == "__main__":
    main()