"""Test cases for the Set base class and built-in sets."""

import unittest

import bpy

from synthpic2 import PrototypeLibrary
from synthpic2.recipe.blueprints import ParticleBlueprint
from synthpic2.recipe.registries import clear_all_registries
from synthpic2.recipe.registries import PARTICLE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries import PARTICLE_REGISTRY
from synthpic2.recipe.registries.registries import GEOMETRY_PROTOTYPE_REGISTRY
from synthpic2.recipe.registries.registries import MATERIAL_PROTOTYPE_REGISTRY


class TestParticleBlueprint(unittest.TestCase):
    """Test cases for the ParticleBlueprint class."""

    @classmethod
    def setUpClass(cls) -> None:
        PrototypeLibrary.load()

    @classmethod
    def tearDownClass(cls) -> None:
        clear_all_registries()

    def setUp(self) -> None:
        PARTICLE_REGISTRY.clear()
        PARTICLE_BLUEPRINT_REGISTRY.clear()
        bpy.ops.wm.read_factory_settings()

    def test_invoke(self) -> None:
        """Test invocation of the ParticleBlueprint class."""

        bpy.data.objects["Cube"].name = "MeasurementVolume"

        particle_blueprint = ParticleBlueprint(name="TestBlueprint",
                                               geometry_prototype_name="sphere",
                                               material_prototype_name="plain",
                                               number=1)
        particle_blueprint.invoke()

    def test_wrong_prototype_names(self) -> None:
        """Test invocation of the ParticleBlueprint class with non-existent prototype
        names."""
        with self.assertRaises(KeyError):
            particle_blueprint = ParticleBlueprint(
                name="TestBlueprint",
                geometry_prototype_name="non_existent_prototype_123asd",
                material_prototype_name="plain",
                number=1)
            particle_blueprint.invoke()

        with self.assertRaises(KeyError):
            particle_blueprint = ParticleBlueprint(
                name="TestBlueprint",
                geometry_prototype_name="sphere",
                material_prototype_name="non_existent_prototype_123asd",
                number=1)
            particle_blueprint.invoke()

    def test_gather_feature_subsets(self) -> None:
        """Test the internal method ``_gather_feature_subsets``."""

        # pylint: disable=protected-access

        geometry_prototype_name = "sphere"
        geometry_prototype = GEOMETRY_PROTOTYPE_REGISTRY[geometry_prototype_name]

        material_prototype_name = "plain"
        material_prototype = MATERIAL_PROTOTYPE_REGISTRY[material_prototype_name]

        particle_blueprint = ParticleBlueprint(
            name="TestBlueprint",
            geometry_prototype_name=geometry_prototype_name,
            material_prototype_name=material_prototype_name,
            number=1)

        self.assertIn(particle_blueprint.custom_features,
                      particle_blueprint._gather_feature_subsets())
        self.assertIn(geometry_prototype.features,
                      particle_blueprint._gather_feature_subsets())
        self.assertIn(material_prototype.features,
                      particle_blueprint._gather_feature_subsets())
