"""Module for the Agglomerate classes."""

from copy import copy
from dataclasses import dataclass
from dataclasses import field
from functools import cached_property
from typing import Optional, TypeVar

import bpy
import mathutils    # type: ignore
import matplotlib.pyplot as plt
import numpy as np
import trimesh

from .....blender.utilities import convert_blender_object_to_trimesh
from .....blender.utilities import get_object
from .....blender.utilities import set_parent
from .bounding_box import BoundingBox
from .custom_collision_manager import CustomCollisionManager
from .utilities import flatten_list
from .utilities import get_random_direction
from .utilities import normalize_vector
from .utilities import sample_random_mass_points_in_mesh
from .utilities import validate_3d_vector

# TODO: Note: we could further optimize this, by making `bounding_box` a cached
#   property. However, this is not as straight forwards as it might appear, because of
#   the `transform` method. So it does not seem worthwhile right now. :-)

TAgglomerate = TypeVar("TAgglomerate", bound="Agglomerate")


@dataclass
class Agglomerate:
    """Class to represent agglomerates."""
    mesh_primary_particle: trimesh.Trimesh
    name: str
    _children: list["Agglomerate"] = field(default_factory=list)
    parent: Optional["Agglomerate"] = None

    def __post_init__(self) -> None:
        self.collision_manager = CustomCollisionManager()
        self.collision_manager.add_object(self.name, self.mesh_primary_particle)
        self.transformation = np.identity(4)

    @property
    def children(self) -> list["Agglomerate"]:
        """List of children of this agglomerate.

        Returns:
            list[Agglomerate]: List of children of this Agglomerate.
        """
        return self._children

    def get_descendant(self, descendant_name: str) -> "Agglomerate":
        """Retrieves a descendant with the given name.

        Args:
            descendant_name (str): name of the descendant to retrieve

        Raises:
            IndexError: if no such descendant exists

        Returns:
            Agglomerate: descendant with the given name
        """
        try:
            descendant = [
                descendant for descendant in self.all_descendants
                if descendant.name == descendant_name
            ][0]
        except IndexError as error:
            raise IndexError(
                f"There is no descendant with name '{descendant_name}' in agglomerate "
                f"'{self.name}'.") from error

        return descendant

    def add_child(self, child: "Agglomerate") -> None:
        """Add a child to the agglomerate.

        Args:
            child (Agglomerate): new child
        """
        self._children.append(child)
        child.parent = self

        self.collision_manager.merge(child.collision_manager)

        # Reset cached properties.
        self.delete_attributes("center_mass", "bounding_box")

    def export(self, path: str) -> None:
        """Export the mesh of the agglomerate (including its descendants) as an stl
            file.

        Args:
            path (str): Path to the output stl file.
        """
        self.mesh.export(path)

    def plot(self) -> None:
        """Plot the mesh of the agglomerate (including its descendants)."""
        mesh = self.mesh
        ax = plt.gca()
        xs = mesh.vertices[:, 0]
        ys = mesh.vertices[:, 1]
        zs = mesh.vertices[:, 2]
        ax.plot_trisurf(xs, ys, triangles=mesh.faces, Z=zs)
        ax.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))

    @property
    def mesh(self) -> trimesh.Trimesh:
        """Retrieves the concatenated mesh of all descendants, i.e. primary particles.

        Returns:
            trimesh.Trimesh: Concatenated mesh of all primary particles
        """
        all_meshes = [
            agglomerate.mesh_primary_particle for agglomerate in self.all_descendants
        ]
        return trimesh.util.concatenate(all_meshes)

    @property
    def num_children(self) -> int:
        """Number of children.

        Returns:
            int: Number of children.
        """
        return len(self._children)

    @property
    def all_descendants(self: TAgglomerate) -> list[TAgglomerate]:
        """List of all descendants (primary particles) of the agglomerate, i.e. itself,
            its children, its children's children, etc.

        Returns:
            list[Agglomerate]: List of all descendants of the agglomerate.
        """
        return [self] + flatten_list([child.all_descendants for child in self.children])

    @property
    def num_descendants(self) -> int:
        """Number of descendants of the agglomerate.

        Returns:
            int: Number of descendants of the Agglomerate.
        """
        return len(self.all_descendants)

    @cached_property
    def bounding_box(self) -> BoundingBox:
        """Bounding box of the Agglomerate (including all descendants).

        Returns:
            BoundingBox: _description_
        """
        mesh_bounds = self.mesh.bounds
        extents = mesh_bounds[1, :] - mesh_bounds[0, :]
        coordinate = mesh_bounds[0, :]
        return BoundingBox(extents=extents, location=coordinate)

    @property
    def centroid(self) -> np.ndarray:
        """Centroid of the agglomerate (including all descendants).

        Returns:
            np.ndarray: Centroid of the Agglomerate.
        """
        return np.asarray(self.mesh.centroid)

    @cached_property
    def center_mass(self) -> np.ndarray:
        """Center of mass of the agglomerate (including all descendants).

        Returns:
            np.ndarray: Center of mass.
        """
        return np.asarray(self.mesh.center_mass)

    @property
    def centroid_primary_particle(self) -> np.ndarray:
        """Centroid of the agglomerates ultimate primary particle, i.e. disregarding its
            children.

        Returns:
            np.ndarray: Centroid of the agglomerates ultimate primary particle
        """
        return np.asarray(self.mesh_primary_particle.centroid)

    @property
    def mass(self) -> float:
        """Mass of the agglomerate (including all descendants).

        Returns:
            float: Mass of the agglomerate
        """
        return sum(
            abs(descendant.mesh_primary_particle.mass)
            for descendant in self.all_descendants)

    def is_overlapping(self, agglomerate_other: "Agglomerate") -> bool:
        """Check if two agglomerates (including their descendants) overlap."""
        tf = self.collision_manager.in_collision_other(
            agglomerate_other.collision_manager)

        assert isinstance(tf, bool)

        return tf

    def get_collision_partners(
            self,
            agglomerate_other: "Agglomerate") -> tuple["Agglomerate", "Agglomerate"]:
        """Get overlapping primary particles for a pair of overlapping agglomerates.

        Returns:
            tuple[Agglomerate, Agglomerate]: Pair of overlapping primary particles.
        """
        collision_results = self.collision_manager.in_collision_other(
            agglomerate_other.collision_manager, return_names=True)
        assert isinstance(collision_results, tuple)

        primary_particle_name_self, primary_particle_name_other = \
            list(collision_results[1])[0]

        return (self.get_descendant(primary_particle_name_self),
                agglomerate_other.get_descendant(primary_particle_name_other))

    @classmethod
    def from_blender(cls, blender_object: bpy.types.Object) -> "Agglomerate":
        """Create an Agglomerate from a blender object, by converting it to a trimesh.
            The name is adopted.

        Returns:
            Agglomerate: Agglomerate
        """
        mesh = convert_blender_object_to_trimesh(blender_object)
        return Agglomerate(mesh_primary_particle=mesh, name=blender_object.name)

    def to_blender(self) -> None:
        """Transfer the transformations of the primary particles of an Agglomerate to
            the corresponding blender objects."""

        # Transfer transformations from trimesh to blender objects.
        for descendant in self.all_descendants:
            transformation = mathutils.Matrix(descendant.transformation)
            blender_object = get_object(descendant.name)
            blender_object.matrix_basis = transformation

        # Establish same parent-child relationships for blender objects as in trimesh.
        for descendant in self.all_descendants:
            if descendant.parent is not None:    # all agglomerates except self
                descendant_object = get_object(descendant.name)
                parent_object = get_object(descendant.parent.name)
                set_parent(descendant_object, parent_object, keep_transform=True)

        # blender_object_ultimate_parent["agglomerate_mass"] = self.mass

    @cached_property
    def radius_gyration_primary_particle(self) -> float:
        """Radius of gyration of a primary particle with arbitrary shape. Calculated
            from randomly sampled mass points in the mesh.

        Returns:
            float: Radius of gyration of a primary particle with arbitrary shape.
        """

        num_random_points = 100

        mass_points, masses = sample_random_mass_points_in_mesh(
            mesh=self.mesh_primary_particle, count=num_random_points)

        return self._calculate_radius_gyration(self.center_mass, mass_points, masses)

    @staticmethod
    def _calculate_radius_gyration(center_mass: np.ndarray, mass_points: np.ndarray,
                                   masses: np.ndarray) -> float:
        """Calculate the radius of gyration of a cloud of mass points.

        Based on: https://www.engineeringtoolbox.com/moment-inertia-torque-d_913.html

        Args:
            center_mass (np.ndarray): Center of mass of the cloud.
            mass_points (np.ndarray): Mass points.
            masses (np.ndarray): Masses of the points.

        Returns:
            float: Radius of gyration.
        """
        squared_distances = np.sum((mass_points - center_mass)**2, axis=1)
        moment_inertia = np.sum(np.dot(squared_distances, masses))
        radius_gyration = np.sqrt(moment_inertia / np.sum(masses))
        return radius_gyration

    @property
    def radius_gyration(self) -> float:
        """Radius of gyration of an agglomerate (including its descendants).

        If the agglomerate has no descendants, then the radius of gyration is determined
        by random sampling of mass points. Else, the centers of mass and the masses of
        the descendants are used.

        Returns:
            float: Radius of gyration.
        """
        if self.num_children == 0:
            return self.radius_gyration_primary_particle
        else:
            mass_points = np.asarray([
                descendant.mesh_primary_particle.center_mass
                for descendant in self.all_descendants
            ])
            masses = np.asarray([
                descendant.mesh_primary_particle.mass
                for descendant in self.all_descendants
            ])

            return self._calculate_radius_gyration(self.center_mass, mass_points,
                                                   masses)

    def apply_periodic_boundaries(self, space_bounding_box: BoundingBox) -> None:
        """Apply periodic boundaries of a box-shaped simulation space to the
            agglomerate, by translating it, if it is outside of the simulation space.

        Args:
            space_bounding_box (BoundingBox): Bounding box of the simulation space.
        """
        centroid_distance_vector = (self.bounding_box.centroid -
                                    space_bounding_box.centroid)
        is_outside_bounding_box = np.abs(centroid_distance_vector) > (
            self.bounding_box.extents + space_bounding_box.extents) / 2
        translation_vector = (-1 * is_outside_bounding_box *
                              space_bounding_box.extents *
                              np.sign(centroid_distance_vector))
        self.translate(translation_vector)

    def translate(self,
                  translation_vector: np.ndarray | list | tuple,
                  do_reverse: bool = False) -> None:
        """Translate the agglomerate (including all the descendants).

        Args:
            translation_vector (np.ndarray | list | tuple): Translation vector
            do_reverse (bool, optional): If true, applies the inverse translation.
                Defaults to False.
        """
        translation_vector = validate_3d_vector(translation_vector)

        if do_reverse:
            translation_vector = -translation_vector

        transformation = np.asarray(mathutils.Matrix.Translation(translation_vector))

        self.transform(transformation)

    def rotate_around_center_mass(self,
                                  rotation_vector_deg: np.ndarray | list | tuple,
                                  do_reverse: bool = False) -> None:
        """Rotate the agglomerate (including all descendants) around its center of mass,
            according to the specified angles.

        Args:
            rotation_vector_deg (np.ndarray | list | tuple): Rotation angles in degree,
                in x-, y- and z- direction.
            do_reverse (bool, optional): If true, applies the inverse rotation.
                Defaults to False.
        """
        rotation_vector_deg = validate_3d_vector(rotation_vector_deg)

        # Legend:
        # r_i - Rotation matrix (always around origin)
        # t_i - Translation matrix

        if not np.any(rotation_vector_deg):
            return

        rotation_vector_rad = np.deg2rad(rotation_vector_deg)

        if do_reverse:
            rotation_vector_rad = -rotation_vector_rad

        t_to_origin = mathutils.Matrix.Translation(-self.center_mass)
        t_from_origin = mathutils.Matrix.Translation(self.center_mass)
        r_x = mathutils.Matrix.Rotation(rotation_vector_rad[0], 4, "X")
        r_y = mathutils.Matrix.Rotation(rotation_vector_rad[1], 4, "Y")
        r_z = mathutils.Matrix.Rotation(rotation_vector_rad[2], 4, "Z")

        if do_reverse:
            r_total = r_z @ r_y @ r_x
        else:
            r_total = r_x @ r_y @ r_z

        transformation = t_from_origin @ r_total @ t_to_origin

        self.transform(np.asarray(transformation), do_update_center_mass=False)

    def transform(self,
                  transform: np.ndarray,
                  do_update_center_mass: bool = True) -> None:
        """Transform the agglomerate (including all descendants).

        Args:
            transform (np.ndarray): Transformation matrix (4x4).
            do_update_center_mass (bool, optional): If true, then update the centers of
                mass of all descendants. Defaults to True.
        """
        for descendant in self.all_descendants:
            descendant.mesh_primary_particle.apply_transform(transform)
            self.collision_manager.transform_object(descendant.name, transform)
            descendant.transformation = transform @ descendant.transformation

            # Make update of centers of mass optional, since it is costly and not
            # necessary for rotations around the center of mass.
            if do_update_center_mass:
                descendant.center_mass = trimesh.transform_points(
                    np.array([
                        descendant.center_mass,
                    ]), transform)[0]

            descendant.delete_attributes("bounding_box")

    def delete_attributes(self, *attribute_names: str) -> None:
        """Delete a list of attributes. Used to reset cached properties."""
        for attribute_name in attribute_names:
            try:
                delattr(self, attribute_name)
            except AttributeError:
                pass

    def initialize_collision(self, agglomerate_other: "Agglomerate") -> None:
        """Initialize a collision by randomly rotating the collision partners and
            placing them into each others proximity, so that their bounding boxes touch.

        Args:
            agglomerate_other (Agglomerate): Collision partner.
        """
        self.rotate_around_center_mass(np.random.uniform(0, 360, (3,)))
        agglomerate_other.rotate_around_center_mass(np.random.uniform(0, 360, (3,)))
        bbox_a = self.bounding_box
        bbox_b = agglomerate_other.bounding_box
        bbox_stitching_face_normal_a = bbox_a.get_random_boundingbox_face()
        bbox_stitching_face_normal_b = -bbox_stitching_face_normal_a
        stitching_point_a = bbox_a.get_random_point_boundingbox_face(
            desired_face_normal=bbox_stitching_face_normal_a)
        stitching_point_b = bbox_b.get_random_point_boundingbox_face(
            desired_face_normal=bbox_stitching_face_normal_b)
        translation_vector = stitching_point_a - stitching_point_b
        agglomerate_other.translate(translation_vector)

    def collide(self,
                agglomerate_other: "Agglomerate",
                translation_speed: float,
                randomness: float,
                sintering_ratio: float = 0,
                rotation_speed: float = 0) -> None:
        """Collide the agglomerate with another agglomerate.

        Args:
            agglomerate_other (Agglomerate): Collision partner.
            translation_speed (float): Relative translation step size, between two
                collision checks.
            randomness (float): Number between 0 and 1, to control the randomness of the
                random walk:
                    0 = straight translation, constant rotation
                    1 = completely random walk, stochastic rotation
            sintering_ratio (float, optional): Number between 0 and 1, to control how
                close the centers of mass of the two touching primary particles will be
                after the collision:
                    0 = particles will just barely touch after the collision
                    1 = centers of mass will be identical
                Defaults to 0.
            rotation_speed (float, optional): Sum of the rotation intervals in x-, y-
                and z-direction between two collision checks, for both collision
                partners, as fraction of 360 degrees.
                Defaults to 0.
        """

        self.initialize_collision(agglomerate_other)

        # Set up translation and rotation.
        do_random_movement = (randomness > 0)

        collision_direction = get_random_direction()
        rotation_angles_random_other = normalize_vector(np.random.uniform(
            0, 1, (3,))) * 360 * rotation_speed
        rotation_angles_random_self = normalize_vector(np.random.uniform(
            0, 1, (3,))) * 360 * rotation_speed

        translation_direction_straight = collision_direction
        translation_direction = translation_direction_straight
        translation_vector = translation_direction * translation_speed

        # Set up a box-shaped simulation space, to use as periodic boundaries
        simulation_space = copy(self.bounding_box)
        simulation_space.enlarge(agglomerate_other.bounding_box)

        # Store original position of agglomerate_other and track the total translation
        # vector, so the simulation can be reset later on, if the collision gets stuck
        # in a long loop.
        original_position_other = agglomerate_other.centroid
        total_translations_vector = np.zeros(3)

        # Move and rotate agglomerate_other and rotate self until there is a collision.
        while not self.is_overlapping(agglomerate_other):

            if any(np.abs(total_translations_vector) > 2 * simulation_space.extents):
                # Safety net, to avoid an infinite loop for worst-case translation
                # directions.
                offset = agglomerate_other.centroid - original_position_other
                agglomerate_other.translate(-offset)
                total_translations_vector = np.zeros(3)

                translation_direction_straight = get_random_direction()
                translation_direction = translation_direction_straight

            agglomerate_other.apply_periodic_boundaries(simulation_space)

            if do_random_movement:
                translation_direction_random = get_random_direction()
                translation_direction = (
                    (1 - randomness) * translation_direction_straight +
                    randomness * translation_direction_random)

                rotation_angles_random_other = normalize_vector(
                    np.random.uniform(0, 1, (3,))) * 360 * rotation_speed
                rotation_angles_random_self = normalize_vector(
                    np.random.uniform(0, 1, (3,))) * 360 * rotation_speed

            translation_direction = normalize_vector(translation_direction)
            translation_vector = translation_direction * translation_speed

            agglomerate_other.translate(translation_vector)
            total_translations_vector += translation_vector

            agglomerate_other.rotate_around_center_mass(rotation_angles_random_other)
            self.rotate_around_center_mass(rotation_angles_random_self)

        # Get and store, which primary particles collide, to adjust sintering ratio
        # later. We do this here, because here we *know* that there is a collision,
        # which might be undone by the rewinding.
        collision_partner_self, collision_partner_other = self.get_collision_partners(
            agglomerate_other)

        # Rewind the collision, to just get point contacts.
        original_translation_vector = translation_vector
        original_rotation_angles_other = rotation_angles_random_other
        original_rotation_angles_self = rotation_angles_random_self

        # Revert last step, i.e. *no* overlap
        self.rotate_around_center_mass(original_rotation_angles_self, do_reverse=True)
        agglomerate_other.rotate_around_center_mass(original_rotation_angles_other,
                                                    do_reverse=True)
        agglomerate_other.translate(original_translation_vector, do_reverse=True)

        # step_fraction=0 means position before the last step, i.e. guaranteed *no*
        #   overlap
        # step_fraction=1 means position after the last step, i.e. guaranteed overlap
        step_fraction_max = 1.0
        step_fraction_min = 0.0

        num_substep_iterations = 10
        for substep_index in range(num_substep_iterations + 1):
            step_fraction = (step_fraction_max + step_fraction_min) / 2

            translation_vector = original_translation_vector * step_fraction
            rotation_angles_other = original_rotation_angles_other * step_fraction
            rotation_angles_self = original_rotation_angles_self * step_fraction

            agglomerate_other.translate(translation_vector)
            agglomerate_other.rotate_around_center_mass(rotation_angles_other)
            self.rotate_around_center_mass(rotation_angles_self)

            is_last_step = substep_index == num_substep_iterations

            if is_last_step:
                break

            if self.is_overlapping(agglomerate_other):
                step_fraction_max = step_fraction
            else:
                step_fraction_min = step_fraction

            self.rotate_around_center_mass(rotation_angles_self, do_reverse=True)
            agglomerate_other.rotate_around_center_mass(rotation_angles_other,
                                                        do_reverse=True)
            agglomerate_other.translate(translation_vector, do_reverse=True)

        # Set sintering ratio.
        if sintering_ratio > 0:
            distance_vector = (collision_partner_self.center_mass -
                               collision_partner_other.center_mass)
            agglomerate_other.translate(distance_vector * sintering_ratio)

        self.add_child(agglomerate_other)
