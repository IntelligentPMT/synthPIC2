"""Tests of the Blender utilities."""

import pathlib
import unittest

import bpy
import numpy as np

from synthpic2 import blender
from synthpic2.blender.utilities import convert_blender_object_to_trimesh
from synthpic2.blender.utilities import create_collection
from synthpic2.blender.utilities import create_emission_shader
from synthpic2.blender.utilities import duplicate_and_link_object
from synthpic2.blender.utilities import get_collection
from synthpic2.blender.utilities import get_material
from synthpic2.blender.utilities import get_object
from synthpic2.blender.utilities import replace_object_material
from synthpic2.blender.utilities import select_only


class BlenderUtilitiesTest(unittest.TestCase):
    """Tests of the Blender utilities."""

    test_image_name = "test_image.png"
    root_directory = pathlib.Path(__file__).parent
    test_image_path = root_directory / f"{test_image_name}"

    @classmethod
    def setUpClass(cls) -> None:
        cls._remove_test_image()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._remove_test_image()

    @classmethod
    def _remove_test_image(cls) -> None:
        cls.test_image_path.unlink(missing_ok=True)

    @classmethod
    def _assert_test_image_exists(cls) -> None:
        if not cls.test_image_path.exists():
            raise AssertionError(f"File does not exist: {cls.test_image_path}")

    def test_render_to_file(self) -> None:
        # Start with a clean scene.
        bpy.ops.wm.read_factory_settings()

        # Speed up the rendering.
        scene = bpy.data.scenes[0]
        scene.eevee.taa_render_samples = 1
        scene.render.resolution_percentage = 1

        blender.render_to_file(self.test_image_path)
        self._assert_test_image_exists()
        self._remove_test_image()

        with self.assertRaises(ValueError):
            blender.render_to_file("invalid_file_format.xyz")

    def test_duplicate_and_link_object(self) -> None:
        bpy.ops.wm.read_factory_settings()

        object_ = bpy.data.objects["Cube"]
        target_collection = bpy.data.collections["Collection"]
        duplicate_name_suffix = "_Duplicate"

        duplicate, _ = duplicate_and_link_object(object_, duplicate_name_suffix,
                                                 target_collection)

        self.assertEqual(duplicate,
                         bpy.data.objects[object_.name + duplicate_name_suffix])

    def test_get_material(self) -> None:
        bpy.ops.wm.read_factory_settings()

        get_material("Material")

        with self.assertRaises(ValueError):
            get_material("NonExistentMaterial")

    def test_get_collection(self) -> None:
        bpy.ops.wm.read_factory_settings()

        get_collection("Collection")

        with self.assertRaises(ValueError):
            get_collection("NonExistentCollection")

    def test_get_object(self) -> None:
        bpy.ops.wm.read_factory_settings()

        get_object("Cube")

        with self.assertRaises(ValueError):
            get_object("NonExistentObject")

    def test_replace_material(self) -> None:
        bpy.ops.wm.read_factory_settings()

        object_ = bpy.data.objects["Cube"]

        replace_object_material(object_, "Material", "Material")

        with self.assertRaises(ValueError):
            replace_object_material(object_, "NonExistentMaterial", "Material")

        with self.assertRaises(ValueError):
            replace_object_material(object_, "Material", "NonExistentMaterial")

    def test_create_ground_truth_emission_shader(self) -> None:
        bpy.ops.wm.read_factory_settings()
        create_emission_shader()

    def test_create_collection(self) -> None:
        bpy.ops.wm.read_factory_settings()

        new_collection_name = "Test"
        create_collection(new_collection_name)
        self.assertTrue(new_collection_name in bpy.data.collections)

        with self.assertRaises(ValueError):
            create_collection("Test")

    def test_convert_blender_object_to_trimesh(self) -> None:
        bpy.ops.wm.read_factory_settings()
        blender_object = bpy.data.objects["Cube"]
        blender_object.rotation_euler = [1, 2, 3]

        select_only(blender_object)
        bpy.ops.object.modifier_add(type="DISPLACE")

        mesh = convert_blender_object_to_trimesh(blender_object)

        # Reference values determined via stl export.
        np.testing.assert_array_almost_equal(mesh.bounding_box.extents,
                                             [4.15816879, 3.57742882, 3.8256073])
        np.testing.assert_array_almost_equal(mesh.bounding_box.centroid, [0, 0, 0])

    def test_convert_blender_quad_object_to_trimesh(self) -> None:
        bpy.ops.wm.read_factory_settings()
        bpy.ops.mesh.primitive_uv_sphere_add()

        blender_object = bpy.data.objects["Sphere"]
        blender_object.rotation_euler = [1, 2, 3]

        select_only(blender_object)
        bpy.ops.object.modifier_add(type="DISPLACE")

        mesh = convert_blender_object_to_trimesh(blender_object)

        # Reference values determined via stl export.
        np.testing.assert_array_almost_equal(mesh.bounding_box.extents,
                                             [2.993983, 2.995212, 2.99767])
        np.testing.assert_array_almost_equal(mesh.bounding_box.centroid, [0, 0, 0])
