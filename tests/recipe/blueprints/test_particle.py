"""Test cases for the Set base class and built-in sets."""

import unittest

import bpy

from synthpic2 import PrototypeLibrary
from synthpic2.recipe.blueprints import ParticleBlueprint
from synthpic2.recipe.registries import clear_all_registries
from synthpic2.recipe.registries import PARTICLE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries import PARTICLE_REGISTRY

# TODO: Write more tests for the `Particle` class.


class TestParticle(unittest.TestCase):
    """Test cases for the Particle class."""

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
        bpy.data.objects["Cube"].name = "MeasurementVolume"

    def test_md5_reproducibility(self) -> None:
        """Test md5 reproducibility of the Particle class."""

        particle_blueprint = ParticleBlueprint(name="TestBlueprint",
                                               geometry_prototype_name="sphere",
                                               material_prototype_name="plain",
                                               number=1)
        particle_blueprint.invoke()
        particle = PARTICLE_REGISTRY[0]

        original_md5 = particle.md5

        self.setUp()

        particle_blueprint.invoke()
        particle = PARTICLE_REGISTRY[0]
        reproduced_md5 = particle.md5
        self.assertEqual(original_md5, reproduced_md5)

    def test_md5_feature_dependency(self) -> None:
        """Test that the md5 of a particle changes, if its features change."""

        particle_blueprint = ParticleBlueprint(name="TestBlueprint",
                                               geometry_prototype_name="sphere",
                                               material_prototype_name="plain",
                                               number=1)
        particle_blueprint.invoke()
        particle = PARTICLE_REGISTRY[0]

        original_md5 = particle.md5

        original_location = particle.features["location"].value
        particle.features["location"].value = original_location

        self.assertEqual(particle.md5, original_md5)

        particle.features["location"].value = (4, 5, 6)
        self.assertNotEqual(particle.md5, original_md5)

        particle.features["location"].value = original_location
        self.assertEqual(particle.md5, original_md5)
