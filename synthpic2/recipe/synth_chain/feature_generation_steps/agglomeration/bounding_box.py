"""Module for the BoundingBox class."""

from dataclasses import dataclass

import numpy as np
import trimesh
from trimesh import sample as trimesh_sample


@dataclass
class BoundingBox:
    """Class to represent bounding boxes."""
    extents: np.ndarray
    location: np.ndarray

    @property
    def mesh(self) -> trimesh.Trimesh:
        """Mesh of the bounding box.

        Returns:
            trimesh.Trimesh: mesh of the bounding box
        """
        mesh = trimesh.primitives.Box(extents=self.extents)

        # Adjust position of bounding box.
        translation_vector = self.location + self.extents / 2
        mesh.apply_translation(translation_vector)
        return mesh

    @property
    def centroid(self) -> np.ndarray:
        """Centroid of the bounding box.

        Returns:
            np.ndarray: centroid
        """
        return self.location + 0.5 * self.extents

    def enlarge(self, other_bounding_box: "BoundingBox") -> None:
        """Enlarge the bounding box, so that it has a margin as big as another bounding
            box.

        Args:
            other_bounding_box (BoundingBox): enlarged bounding box
        """
        self.extents = self.extents + 2 * other_bounding_box.extents
        self.location = self.location - other_bounding_box.extents

    def get_random_boundingbox_face(self) -> np.ndarray:
        """Get a random bounding box face (area weighted), specified by its face normal.

        Returns:
            np.ndarray: Normal vector of the randomly selected bounding box face.
        """
        delta_x = self.extents[0]
        delta_y = self.extents[1]
        delta_z = self.extents[2]
        # Determine probabilities of faces to be selected. The probabilities are
        # proportional to the area of the faces. Opposing faces have identical
        # probabilities.
        probability = np.zeros(3)
        probability[0] = np.random.rand(1) * (delta_y * delta_z)
        probability[1] = np.random.rand(1) * (delta_x * delta_z)
        probability[2] = np.random.rand(1) * (delta_x * delta_y)
        # The opposing faces with the highest probability are selected.
        index_max = np.argmax(probability)
        face_normal = np.zeros(3)
        face_normal[index_max] = 1
        # Select one of the two opposing faces by randomly flipping the face-normal.
        face_normal = (-1)**np.random.randint(1, 3) * face_normal
        return face_normal

    def get_random_point_boundingbox_face(
            self, desired_face_normal: np.ndarray) -> np.ndarray:
        """Get a random point on the face (specified by a face normal) of a boundingbox.

        Args:
            desired_face_normal (np.ndarray): Normal vector of the desired face.

        Returns:
            np.ndarray: Coordinates of the random point.
        """
        face_normals = self.mesh.face_normals
        assert face_normals is not None
        face_normals = np.round(face_normals).astype(int)
        is_relevant_face = np.all(face_normals == desired_face_normal, 1)
        relevant_face_indices = self.mesh.faces[is_relevant_face, :]
        relevant_face_mesh = trimesh.Trimesh(vertices=self.mesh.vertices,
                                             faces=relevant_face_indices)
        random_point = trimesh_sample.sample_surface(mesh=relevant_face_mesh,
                                                     count=1)[0][0]
        return random_point
