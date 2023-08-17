"""Tests of the Feature class."""

import unittest

import bpy

from synthpic2.blender.utilities import get_object
from synthpic2.recipe.prototypes.feature import Feature


class TestFeature(unittest.TestCase):
    """Tests of the Feature class."""

    def setUp(self) -> None:
        super().setUp()
        bpy.ops.wm.read_factory_settings()

    def test_nonblender_feature(self) -> None:

        # pylint: disable=protected-access

        first_value = 1
        feature = Feature("feature")
        feature.value = first_value
        self.assertEqual(feature.value, first_value)

        second_value = "test"
        feature = Feature("feature")
        feature.value = second_value
        self.assertEqual(feature.value, second_value)

    def test_unambiguity(self) -> None:
        with self.assertRaises(ValueError):
            _ = Feature("feature",
                        blender_link="bpy.data.lights['Light'].energy",
                        _value=1)

    def test_blender_link_validation(self) -> None:
        _ = Feature("feature", _value=1)
        _ = Feature("feature", blender_link="bpy.data.lights['Light'].energy")

        with self.assertRaises(ValueError):
            _ = Feature("feature", blender_link="test")

    def test_blender_feature_attribute_read(self) -> None:
        """Test reading of blender feature with attribute."""
        feature = Feature(name="feature",
                          blender_link="bpy.data.lights['Light'].energy")

        self.assertEqual(feature.value, 1000)

    def test_blender_feature_attribute_write(self) -> None:
        """Test writing of blender feature with attribute."""
        feature = Feature(name="feature",
                          blender_link="bpy.data.lights['Light'].energy")

        set_point = 10000
        feature.value = set_point
        self.assertEqual(feature.value, set_point)

    def test_blender_feature_integer_key_read(self) -> None:
        """Test reading of blender feature with integer key."""
        feature = Feature(name="feature", blender_link="bpy.data.collections[0].tag")
        desired_value = bpy.data.collections[0].tag

        self.assertEqual(feature.value, desired_value)

    def test_blender_feature_integer_key_write(self) -> None:
        """Test writing of blender feature with integer key."""
        feature = Feature(name="feature", blender_link="bpy.data.collections[0].tag")

        set_point = False
        feature.value = set_point

        self.assertEqual(bpy.data.collections[0].tag, set_point)

    def test_blender_feature_string_key_read(self) -> None:
        """Test reading of blender feature with string key."""
        bpy.data.objects["Cube"]["test_property"] = 3
        feature = Feature(name="feature",
                          blender_link="bpy.data.objects['Cube']['test_property']")
        desired_value = 42
        feature.value = desired_value

        self.assertEqual(feature.value, desired_value)

    def test_blender_feature_string_key_write(self) -> None:
        """Test writing of blender feature with string key."""
        bpy.data.objects["Cube"]["test_property"] = 0
        feature = Feature(name="feature",
                          blender_link="bpy.data.objects['Cube']['test_property']")

        set_point = 42
        feature.value = set_point

        self.assertEqual(bpy.data.objects["Cube"]["test_property"], set_point)

    def test_blender_link_with_strange_string_key(self) -> None:

        funny_name_1 = "ContiTo_Sapphire.001"
        bpy.data.collections.new(funny_name_1)
        feature_1 = Feature(
            name="feature",
            blender_link=f'bpy.data.collections["{funny_name_1}"].name',
        )
        self.assertEqual(feature_1.value, funny_name_1)

        funny_name_2 = "funny.collection_$123#_name"
        bpy.data.collections.new(funny_name_2)
        feature_2 = Feature(
            name="feature",
            blender_link=f'bpy.data.collections["{funny_name_2}"].name',
        )
        self.assertEqual(feature_2.value, funny_name_2)

    def test_blender_feature_update(self) -> None:

        old_object_name = "Cube"
        new_object_name = "NewCube"

        feature = Feature(name="feature",
                          blender_link=f"bpy.data.objects['{old_object_name}'].scale")

        get_object(old_object_name).name = new_object_name

        renaming_maps = {"Object": {old_object_name: new_object_name}}

        feature.update_blender_link(renaming_maps)

        set_point = (1, 2, 1)

        feature.value = set_point
        obj_ = get_object(new_object_name)
        self.assertEqual(tuple(obj_.scale), set_point)
