"""Test cases for the Set base class and built-in sets."""

import unittest
from unittest.mock import Mock

import bpy
from pyparsing import ParseException

from synthpic2.recipe.process_conditions.feature_criteria import ContainsString
from synthpic2.recipe.process_conditions.feature_criteria import IsEqualTo
from synthpic2.recipe.process_conditions.sets import Set
from synthpic2.recipe.prototypes.feature import Feature
from synthpic2.recipe.registries.registries import PARTICLE_REGISTRY
from synthpic2.recipe.registries.registry import Registry


class TestSet(unittest.TestCase):
    """Test cases for the Set class."""

    def test_set_criterion_parsing(self) -> None:
        """Test parsing of the set criterion."""

        bpy.ops.wm.read_factory_settings()

        particle = Mock()
        particle.name = "Cube"
        particle.features = Registry("Features")
        particle.features.register(
            Feature(name="name", blender_link="bpy.data.objects['Cube'].name"))
        particle.features.register(
            Feature(name="location", blender_link="bpy.data.objects['Cube'].location"))
        PARTICLE_REGISTRY.register(particle)

        _ = ContainsString(name="IsCube",
                           feature_name="name",
                           search_string="Cube",
                           default_return_value=False),
        _ = IsEqualTo(name="IsAtOrigin",
                      feature_name="location",
                      comparand=(0, 0, 0),
                      default_return_value=False),
        _ = ContainsString(name="IsSphere",
                           feature_name="name",
                           search_string="Sphere",
                           default_return_value=False),

        self.assertIs(
            Set(name="TestSet1", criterion="$IsAtOrigin and $IsCube")()[0], particle)

        self.assertEqual(
            len(Set(name="TestSet2", criterion="$IsAtOrigin and $IsSphere")()), 0)

        with self.assertRaises(ParseException):
            Set(name="TestSet3", criterion="$IsAtOrigin and ")()

        with self.assertRaises(ValueError):
            # cspell: disable-next-line
            Set(name="TestSet4", criterion="$IsAtOrigineeeeee and True")()
