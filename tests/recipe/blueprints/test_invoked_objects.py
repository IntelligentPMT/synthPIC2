"""Test the classes of invoked objects: Particle and Measurement Technique."""

import unittest
from unittest import mock

import bpy

from synthpic2.prototype_library import PrototypeLibrary
from synthpic2.recipe.blueprints.blueprints import MeasurementTechnique
from synthpic2.recipe.blueprints.blueprints import \
    MeasurementTechniqueBlueprint
from synthpic2.recipe.blueprints.blueprints import Particle
from synthpic2.recipe.blueprints.blueprints import ParticleBlueprint
from synthpic2.recipe.registries.registries import clear_all_registries
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_REGISTRY
from synthpic2.recipe.registries.registries import PARTICLE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries.registries import PARTICLE_REGISTRY
from synthpic2.utilities import get_object_md5


class _BaseTestClass(unittest.TestCase):
    """Base test class for the tests in this module."""

    @classmethod
    def setUpClass(cls) -> None:
        PrototypeLibrary.load()

    @classmethod
    def tearDownClass(cls) -> None:
        clear_all_registries()

    def setUp(self) -> None:
        PARTICLE_REGISTRY.clear()
        PARTICLE_BLUEPRINT_REGISTRY.clear()
        MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY.clear()
        MEASUREMENT_TECHNIQUE_REGISTRY.clear()
        bpy.ops.wm.read_factory_settings()


class TestParticle(_BaseTestClass):
    """Test the class ``Particle``."""

    def test_md5_property(self) -> None:
        """Test the ``md5`` property."""
        with mock.patch("synthpic2.recipe.blueprints.blueprints.get_object_md5",
                        side_effect=get_object_md5) as mocked:
            particle_blueprint = ParticleBlueprint(name="TestBlueprint",
                                                   geometry_prototype_name="sphere",
                                                   material_prototype_name="plain",
                                                   number=1)
            particle = Particle(name="TestParticle", blueprint=particle_blueprint)
            self.assertIsInstance(particle.md5, str)

        mocked.assert_called_once()


class TestMeasurementTechnique(_BaseTestClass):
    """Test the class ``MeasurementTechnique``."""

    def test_attrs_post_init(self) -> None:
        """Test the internal method ``__attrs_post_init__``."""
        measurement_technique_blueprint = MeasurementTechniqueBlueprint(
            name="TestBlueprint_1",
            measurement_technique_prototype_name="secondary_electron_microscope",
            measurement_volume_material_prototype_name="vacuum")
        self.assertNotIn("output_root", measurement_technique_blueprint.features)

        measurement_technique = MeasurementTechnique(
            name="TestMeasurementTechnique_1",
            blueprint=measurement_technique_blueprint)
        self.assertIn("output_root", measurement_technique.features)

    def test_prepare_for_render(self) -> None:
        """Test the method ``prepare_for_render``."""

        # pylint: disable=line-too-long

        measurement_technique_blueprint = MeasurementTechniqueBlueprint(
            name="TestBlueprint_2",
            measurement_technique_prototype_name="secondary_electron_microscope",
            measurement_volume_material_prototype_name="vacuum")
        measurement_technique_blueprint.measurement_technique_prototype.prepare_for_render = (    # type: ignore
            mock.Mock())

        measurement_technique = MeasurementTechnique(
            name="TestMeasurementTechnique_2",
            blueprint=measurement_technique_blueprint)
        rendering_mode = "test_rendering_mode"
        measurement_technique.prepare_for_render(rendering_mode)

        measurement_technique_blueprint.measurement_technique_prototype.prepare_for_render.assert_called_once_with(    # type: ignore
            rendering_mode)
