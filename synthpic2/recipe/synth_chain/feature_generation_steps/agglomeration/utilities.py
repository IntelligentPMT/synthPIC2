"""Module for agglomeration utilities."""

import numpy as np
import trimesh
import trimesh.sample as trimesh_sample


def validate_3d_vector(vector: np.ndarray | list | tuple) -> np.ndarray:
    """Validate 3d vector.

    Args:
        vector (np.ndarray | list | tuple): vector in different data types

    Raises:
        ValueError: If vector has not exactly 3 elements.

    Returns:
        np.ndarray: vector as numpy array
    """
    sanitized_vector = np.asarray(vector)
    if sanitized_vector.shape != (3,):
        raise ValueError("Expected vector to have exactly three elements.")

    return sanitized_vector


def sample_random_mass_points_in_mesh(mesh: trimesh.Trimesh,
                                      count: int) -> tuple[np.ndarray, np.ndarray]:
    """Sample random points inside of a mesh. The specified `count` is not matched
        exactly.

    Args:
        mesh (trimesh.Trimesh): Mesh to sample from.
        count (int): Approximate number of points

    Returns:
        tuple[np.ndarray, np.ndarray]: Number of points and associated weights.
    """
    points = trimesh_sample.volume_mesh(mesh=mesh, count=count)
    num_points = len(points)

    if len(points) > 0:
        masses = np.ones(num_points) * mesh.mass / num_points
    else:
        points, masses = sample_random_mass_points_in_mesh(mesh, count)
    return points, masses


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def get_random_direction() -> np.ndarray:
    return normalize_vector(np.random.randn(3))


def flatten_list(l: list[list]) -> list:
    return [item for sublist in l for item in sublist]
