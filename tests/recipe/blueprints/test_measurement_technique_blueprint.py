"""Test cases for the Set base class and built-in sets."""

import unittest
from unittest import mock

import bpy

from synthpic2 import PrototypeLibrary
from synthpic2.blender.utilities import duplicate_and_assign_material
from synthpic2.blender.utilities import get_object
from synthpic2.recipe.blueprints.blueprints import \
    MeasurementTechniqueBlueprint
from synthpic2.recipe.prototypes.prototypes import MaterialPrototype
from synthpic2.recipe.prototypes.prototypes import \
    MeasurementTechniquePrototype
from synthpic2.recipe.registries import clear_all_registries
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_REGISTRY


class TestMeasurementTechniqueBlueprint(unittest.TestCase):
    """Test cases for the TestMeasurementTechniqueBlueprint class."""

    # TODO: Use a more generic measurement technique, when one is available.

    # pylint: disable=line-too-long

    @classmethod
    def setUpClass(cls) -> None:
        PrototypeLibrary.load()

    @classmethod
    def tearDownClass(cls) -> None:
        clear_all_registries()

    def setUp(self) -> None:
        MEASUREMENT_TECHNIQUE_REGISTRY.clear()
        MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY.clear()
        bpy.ops.wm.read_factory_settings()

    def test_attrs_post_init(self) -> None:
        """Test the `__attrs_post_init__` method."""

        with mock.patch(
                "synthpic2.recipe.blueprints.blueprints._Blueprint.__attrs_post_init__"
        ) as mocked_base_attrs:
            measurement_technique_blueprint = MeasurementTechniqueBlueprint(
                name="TestBlueprint",
                measurement_technique_prototype_name="secondary_electron_microscope",
                measurement_volume_material_prototype_name="vacuum")

        # Test that post initialization, the measurement technique prototype and its
        # material prototype will be queried from the corresponding registries.
        self.assertIsInstance(
            measurement_technique_blueprint.measurement_technique_prototype,
            MeasurementTechniquePrototype)
        self.assertIsInstance(
            measurement_technique_blueprint.measurement_volume_material_prototype,
            MaterialPrototype)

        # Test that the post init method calls the post init of its base class
        mocked_base_attrs.assert_called_once()

    @mock.patch("synthpic2.recipe.blueprints.blueprints.get_object",
                side_effect=get_object)
    @mock.patch("synthpic2.recipe.blueprints.blueprints.duplicate_and_assign_material",
                side_effect=duplicate_and_assign_material)
    @mock.patch(
        "synthpic2.recipe.blueprints.MeasurementTechnique.update_feature_blender_links")
    def test_invoke(self, mocked_update_blender_link: mock.Mock,
                    mocked_duplicate: mock.Mock, mocked_get_object: mock.Mock) -> None:
        """Test invocation of the MeasurementTechniqueBlueprint class."""

        mt_blueprint = MeasurementTechniqueBlueprint(
            name="TestBlueprint",
            measurement_technique_prototype_name="secondary_electron_microscope",
            measurement_volume_material_prototype_name="vacuum")

        # Mock the methods and functions called inside the invoke method with the
        # original side effects, thus allowing uninterrupted/original program flow
        mt_blueprint.measurement_technique_prototype.initialize = mock.Mock(
            side_effect=mt_blueprint.measurement_technique_prototype.initialize)
        mt_blueprint.measurement_technique_prototype.setup_after_invocation = mock.Mock(
            side_effect=mt_blueprint.measurement_technique_prototype.
            setup_after_invocation)
        mt_blueprint.measurement_volume_material_prototype.append = mock.Mock(
            side_effect=mt_blueprint.measurement_volume_material_prototype.append)

        # Actual call to invoke
        mt_blueprint.invoke()

        # Assert function calls
        mt_blueprint.measurement_technique_prototype.initialize.assert_called_once()
        mt_blueprint.measurement_technique_prototype.setup_after_invocation.assert_called_once(
        )
        mt_blueprint.measurement_volume_material_prototype.append.assert_any_call()
        assert mt_blueprint.measurement_volume_material_prototype.append.call_count == 2
        mocked_get_object.assert_has_calls([
            mock.call("MeasurementVolume"),
            mock.call("Substrate"),
        ])
        mocked_duplicate.assert_has_calls([
            mock.call(bpy.data.objects["MeasurementVolume"],
                      "vacuum",
                      suffix="MeasurementVolume"),
            mock.call(bpy.data.objects["Substrate"], "vacuum", suffix="Substrate")
        ])
        mocked_update_blender_link.assert_has_calls([
            mock.call({"Material": {
                "vacuum": "vacuumMeasurementVolume"
            }}),
            mock.call({"Material": {
                "vacuum": "vacuumSubstrate"
            }})
        ])

    def test_wrong_prototype_names(self) -> None:
        """
        Test invocation of the ParticleBlueprint class with non-existent prototype names.
        """
        with self.assertRaises(KeyError):
            MeasurementTechniqueBlueprint(
                name="TestBlueprint",
                measurement_technique_prototype_name="non_existent_prototype_123asd",
                measurement_volume_material_prototype_name="vacuum")

        with self.assertRaises(KeyError):
            MeasurementTechniqueBlueprint(
                name="TestBlueprint",
                measurement_technique_prototype_name="secondary_electron_microscope",
                measurement_volume_material_prototype_name=
                "non_existent_prototype_123asd")
