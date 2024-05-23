class PathPlanner2():
    def __init__(
        self,
        dataset_path: str,
        floor_height: float,
        ceil_height: float,
        resolution: float = 0.1,
        occ_avoid_radius: float = 0.2,
        conservative: bool = True,
        heuristic: Heuristic = 'euclidean',
        cache_dir = None
    ) -> None:
        self.occ_avoid_radius = occ_avoid_radius
        self.resolution = resolution
        self.occ_avoid = math.ceil((self.occ_avoid_radius) / self.resolution)

        # Gets the map from the parent class.
        # for now we assume all dataset is r3d dataset, so key is set to 'r3d'
        self.dataset = get_posed_rgbd_dataset(key='r3d', path = dataset_path)
        self.occupancy_map = get_occupancy_map_from_dataset(
            self.dataset,
            resolution,
            (floor_height, ceil_height),
            occ_avoid = self.occ_avoid,
            conservative = conservative
        )

        # Initializes the AStarPlanner using the occupancy map.
        is_occ = np.expand_dims((self.occupancy_map.grid == -1), axis = -1)
        self.a_star_planner = AStarPlanner(
            is_occ=is_occ,
            origin=self.occupancy_map.origin,
            resolution=self.occupancy_map.resolution,
            heuristic=heuristic,
        )

    def plan(
        self,
        start_xy: tuple[float, float],
        end_xy: tuple[float, float],
        remove_line_of_sight_points: bool = True,
        num_alternatives: int = 3
    ) -> list[list[tuple[float, float, float]]]:
        primary_path = self._compute_path(start_xy, end_xy, remove_line_of_sight_points)
        alternative_paths = [primary_path]
        
        for _ in range(num_alternatives - 1):
            # Perturb end point slightly to get alternative paths
            perturbed_end_xy = (end_xy[0] + np.random.uniform(-0.2, 0.2), end_xy[1] + np.random.uniform(-0.2, 0.2))
            alternative_path = self._compute_path(start_xy, perturbed_end_xy, remove_line_of_sight_points)
            if alternative_path not in alternative_paths:  # Avoid duplicate paths
                alternative_paths.append(alternative_path)
        
        return alternative_paths

    def _compute_path(
        self,
        start_xy: tuple[float, float],
        end_xy: tuple[float, float],
        remove_line_of_sight_points: bool = True
    ) -> list[tuple[float, float, float]]:
        end_xy, end_theta = self.get_end_xy(start_xy, end_xy)
        waypoints = self.a_star_planner.run_astar(
            start_xy=start_xy,
            end_xy=end_xy,
            remove_line_of_sight_points=remove_line_of_sight_points,
        )
        xyt_points = []
        for i in range(len(waypoints) - 1):
            theta = compute_theta(waypoints[i][0], waypoints[i][1], waypoints[i + 1][0], waypoints[i + 1][1])
            xyt_points.append((waypoints[i][0], waypoints[i][1], float(theta)))
        xyt_points.append((waypoints[-1][0], waypoints[-1][1], end_theta))
        return xyt_points

    def get_end_xy(self, start_xy: tuple[float, float], end_xy: tuple[float, float]):
        start_pt = self.a_star_planner.to_pt(start_xy)
        reachable_pts = self.a_star_planner.get_reachable_points(start_pt)
        reachable_pts = list(reachable_pts)
        end_pt = self.a_star_planner.to_pt(end_xy)
        avoid = math.ceil((0.3 - self.occ_avoid_radius) / self.resolution)
        ideal_dis = math.floor(0.4 / self.resolution)
        inds = torch.tensor([
            self.a_star_planner.compute_s1(end_pt, reachable_pt) 
            + self.a_star_planner.compute_s2(end_pt, reachable_pt, weight = 8, ideal_dis = ideal_dis)
            + self.a_star_planner.compute_s3(reachable_pt, weight = 8, avoid = avoid)
            for reachable_pt in reachable_pts
        ])
        ind = torch.argmin(inds)
        end_pt = reachable_pts[ind]
        x, y = self.a_star_planner.to_xy(end_pt)

        theta = compute_theta(x, y, end_xy[0], end_xy[1])

        return (float(x), float(y)), float(theta)

    def is_valid_starting_point(self, xy: tuple[float, float]) -> bool:
        return self.a_star_planner.is_valid_starting_point(xy)
