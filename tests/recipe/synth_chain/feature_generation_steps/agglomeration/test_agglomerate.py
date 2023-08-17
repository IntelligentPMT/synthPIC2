"""Tests for the particle agglomeration."""

import unittest

import bpy
import numpy as np
import trimesh
from trimesh import creation as trimesh_creation

from synthpic2.blender.utilities import delete
from synthpic2.blender.utilities import select_only
from synthpic2.recipe.synth_chain.feature_generation_steps.agglomeration.agglomerate import \
    Agglomerate
from synthpic2.recipe.synth_chain.feature_generation_steps.agglomeration.agglomerate import \
    sample_random_mass_points_in_mesh
from synthpic2.recipe.synth_chain.feature_generation_steps.agglomeration.agglomeration_simulation import \
    cluster_cluster_agglomeration
from synthpic2.recipe.synth_chain.feature_generation_steps.agglomeration.agglomeration_simulation import \
    particle_cluster_agglomeration
from synthpic2.utilities import seed_everything


class TestAgglomerate(unittest.TestCase):
    """Tests of the `Agglomerate` class."""

    test_agglomerate: Agglomerate

    @classmethod
    def setUpClass(cls) -> None:
        seed_everything(42)
        num_particles = 5
        num_subdivisions = 2
        radii = np.random.uniform(low=10.0, high=20.0, size=num_particles)

        agglomerates: list[Agglomerate] = []

        for particle_id, radius in enumerate(radii):
            agglomerate = cls._get_spherical_agglomerate(
                radius=radius,
                name=f"Particle{particle_id}",
                num_subdivisions=num_subdivisions)
            agglomerates.append(agglomerate)

        cls.test_agglomerate = particle_cluster_agglomeration(agglomerates,
                                                              translation_speed=10,
                                                              randomness=0)

    @staticmethod
    def _get_spherical_agglomerate(
        name: str,
        radius: float = 1.0,
        num_subdivisions: int = 2,
    ) -> Agglomerate:
        mesh = trimesh_creation.icosphere(num_subdivisions, radius=radius)
        return Agglomerate(mesh_primary_particle=mesh, name=name)

    def test_num_children(self) -> None:
        """Test the `num_children` property."""

        agglomerate = self._get_spherical_agglomerate(radius=1, name="TestAgglomerate")
        self.assertEqual(agglomerate.num_children, 0)

    def test_num_descendants(self) -> None:
        """Test the `num_descendants` property."""

        agglomerate = self._get_spherical_agglomerate(radius=1, name="TestAgglomerate")
        self.assertEqual(agglomerate.num_descendants, 1)

    def test_bounding_box(self) -> None:
        """Test the `bounding_box` property."""

        radius = 1

        agglomerate = self._get_spherical_agglomerate(radius=radius,
                                                      name="TestAgglomerate")

        np.testing.assert_array_equal(agglomerate.bounding_box.extents,
                                      [radius * 2, radius * 2, radius * 2])
        np.testing.assert_array_equal(agglomerate.bounding_box.location,
                                      [-radius, -radius, -radius])

    def test_radius_gyration(self) -> None:
        """Test the `radius_gyration` property.

        Source of radius_gyration_target:
            https://lsinstruments.ch/en/theory/static-light-scattering-sls/radius-of-gyration
        """

        def calculate_radius_gyration_reference(mesh: trimesh.Trimesh) -> float:
            num_random_points = 1000
            random_points, weights = sample_random_mass_points_in_mesh(
                mesh=mesh, count=num_random_points)
            squared_distance = np.sum((random_points - mesh.center_mass)**2, axis=1)

            # Moment of inertia (see:
            # https://www.engineeringtoolbox.com/moment-inertia-torque-d_913.html)
            moment_inertia = np.sum(np.dot(squared_distance, weights))
            return np.sqrt(moment_inertia / np.sum(weights))

        radius_gyration_reference = calculate_radius_gyration_reference(
            self.test_agglomerate.mesh)
        delta_percentage = 0.1

        self.assertAlmostEqual(self.test_agglomerate.radius_gyration,
                               radius_gyration_reference,
                               delta=radius_gyration_reference * delta_percentage)

        radius = 1
        radius_gyration_target = (3 * radius**2 / 5)**0.5

        agglomerate = self._get_spherical_agglomerate(radius=radius,
                                                      name="TestAgglomerate")

        self.assertAlmostEqual(agglomerate.radius_gyration,
                               radius_gyration_target,
                               delta=0.1)

    def test_init_collision(self) -> None:
        """Test the `init_collision` method."""
        radius_a = 2
        agglomerate_a = self._get_spherical_agglomerate(radius=radius_a,
                                                        name="TestAgglomerateA")
        radius_b = 5
        agglomerate_b = self._get_spherical_agglomerate(radius=radius_b,
                                                        name="TestAgglomerateB")

        agglomerate_a.initialize_collision(agglomerate_b)

        np.testing.assert_array_almost_equal(agglomerate_a.center_mass, [0, 0, 0])
        np.testing.assert_raises(AssertionError, np.testing.assert_array_equal,
                                 agglomerate_b.center_mass, [0, 0, 0])

        # Test, if the centroid distance of the two agglomerates in one of the spatial
        # directions is equal to the sum of the radii (i.e. the bounding boxes touch).
        self.assertTrue(
            np.any(
                np.abs(np.round(agglomerate_b.center_mass)) == (radius_a + radius_b)))

    def test_all_descendants(self) -> None:
        """Test the `all_descendants` property."""

        agglomerate_a = self._get_spherical_agglomerate(name="TestAgglomerateA")
        agglomerate_b = self._get_spherical_agglomerate(name="TestAgglomerateB")
        agglomerate_c = self._get_spherical_agglomerate(name="TestAgglomerateC")
        agglomerate_d = self._get_spherical_agglomerate(name="TestAgglomerateD")
        agglomerate_e = self._get_spherical_agglomerate(name="TestAgglomerateE")

        agglomerate_a.add_child(agglomerate_b)
        agglomerate_a.add_child(agglomerate_c)
        agglomerate_c.add_child(agglomerate_d)
        agglomerate_d.add_child(agglomerate_e)

        self.assertListEqual(
            agglomerate_a.all_descendants,
            [agglomerate_a, agglomerate_b, agglomerate_c, agglomerate_d, agglomerate_e])
        self.assertEqual(agglomerate_a.num_descendants, 5)

    def test_collide(self) -> None:
        """Test the `collide` method."""
        radius_a = 2
        agglomerate_a = self._get_spherical_agglomerate(radius=radius_a,
                                                        name="TestAgglomerateA")
        radius_b = 4
        agglomerate_b = self._get_spherical_agglomerate(radius=radius_b,
                                                        name="TestAgglomerateB")

        agglomerate_a.collide(agglomerate_b, translation_speed=10, randomness=0)
        distance = np.linalg.norm(agglomerate_a.centroid_primary_particle -
                                  agglomerate_b.centroid_primary_particle)
        np.testing.assert_array_almost_equal(distance, radius_a + radius_b, decimal=1)

    def test_from_blender_conversion(self) -> None:
        """Test of the `from_blender` method."""
        bpy.ops.wm.read_factory_settings()
        blender_object = bpy.data.objects["Cube"]
        blender_object.rotation_euler = [1, 2, 3]

        select_only(blender_object)
        bpy.ops.object.modifier_add(type="DISPLACE")

        agglomerate = Agglomerate.from_blender(blender_object)

        self.assertEqual(agglomerate.name, blender_object.name)

        # Reference values determined via stl export.
        np.testing.assert_array_almost_equal(agglomerate.bounding_box.extents,
                                             [4.15816879, 3.57742882, 3.8256073])
        np.testing.assert_array_almost_equal(agglomerate.bounding_box.location,
                                             [-2.0790844, -1.78871441, -1.91280365])

    @unittest.skip("This test takes quite long (~60s) and was primarily designed to"
                   " profile the code.")
    def test_large_agglomeration(self) -> None:
        bpy.ops.wm.read_factory_settings()
        delete(bpy.data.objects["Cube"])
        seed_everything(42)
        num_particles = 100
        # num_subdivisions = 4

        translation_speed = 10
        rotation_speed = 0.5
        sintering_ratio = 0
        randomness = 1

        sizes = np.random.uniform(low=10.0, high=20.0, size=num_particles)
        agglomerates = []

        for particle_id, size in enumerate(sizes):

            # bpy.ops.mesh.primitive_ico_sphere_add(radius=float(size),
            #                                       subdivisions=num_subdivisions)
            # blender_object = bpy.data.objects["Icosphere"]

            # bpy.ops.mesh.primitive_cube_add(size=float(size))
            # blender_object = bpy.data.objects["Cube"]

            bpy.ops.object.metaball_add(type="BALL", radius=size)
            blender_object = bpy.data.objects["Mball"]

            # bpy.ops.mesh.primitive_uv_sphere_add(radius=float(size))
            # blender_object = bpy.data.objects["Sphere"]

            blender_object.name = \
                f"Particle.{particle_id}" if particle_id > 0 else "Particle"
            agglomerates.append(Agglomerate.from_blender(blender_object))

        # mother_agglomerate = particle_cluster_agglomeration(
        #     agglomerates,
        #     translation_speed=translation_speed,
        #     randomness=randomness,
        #     sintering_ratio=sintering_ratio,
        #     rotation_speed=rotation_speed)

        mother_agglomerate = cluster_cluster_agglomeration(
            agglomerates,
            translation_speed=translation_speed,
            randomness=randomness,
            sintering_ratio=sintering_ratio,
            rotation_speed=rotation_speed)

        # Change blender object properties, based on agglomerate properties
        mother_agglomerate.to_blender()

        bpy.ops.wm.save_as_mainfile(filepath="/workspace/output/test.blend")

        mother_agglomerate.export("/workspace/output/new_agglomerate.stl")
