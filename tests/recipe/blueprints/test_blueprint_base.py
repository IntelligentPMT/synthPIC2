"""Test the blueprint base classes."""

import unittest
from unittest import mock

import bpy

from synthpic2.prototype_library import PrototypeLibrary
from synthpic2.recipe.blueprints.blueprints import _Blueprint
from synthpic2.recipe.blueprints.blueprints import _InvokedObject
from synthpic2.recipe.blueprints.blueprints import \
    MeasurementTechniqueBlueprint
from synthpic2.recipe.prototypes.feature import Feature
from synthpic2.recipe.registries.registries import clear_all_registries
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
from synthpic2.recipe.registries.registries import \
    MEASUREMENT_TECHNIQUE_REGISTRY

# pylint: disable=abstract-class-instantiated,protected-access,line-too-long


@mock.patch("synthpic2.recipe.blueprints.blueprints._Blueprint.__abstractmethods__",
            set())
class TestBlueprint(unittest.TestCase):
    """Test the `_Blueprint` base class."""

    def test_attrs_post_init(self) -> None:
        """Test the `__attrs_post_init__` method."""

        _Blueprint._registry = mock.Mock()    # type: ignore
        _Blueprint._registry.register = mock.Mock()
        with mock.patch.object(_Blueprint,
                               "_gather_feature_subsets",
                               return_value=[[Feature(name="custom_feature")]
                                            ]) as mocked_method:
            blueprint = _Blueprint(name="test")    # type: ignore[abstract]

        # Test that the blueprint would register itself post initialization
        blueprint._registry.register.assert_called_once(    # type: ignore[attr-defined]
        )

        # Test that the features are registered at post init step
        mocked_method.assert_called_once()
        self.assertEqual(len(blueprint.features), 1)

        # Test that the blueprint name is added as custom feature
        assert blueprint.custom_features is not None
        self.assertEqual(len(blueprint.custom_features), 1)
        self.assertEqual(blueprint.custom_features[0].value, "test")


@mock.patch("synthpic2.recipe.blueprints.blueprints._InvokedObject.__abstractmethods__",
            set())
class TestInvokedObject(unittest.TestCase):
    """Test the `_InvokedObject` base class."""

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

    @mock.patch(
        "synthpic2.recipe.blueprints.blueprints.SelfRegisteringAttrsMixin.__attrs_post_init__"
    )
    def test_attrs_post_init(self, mocked_super: mock.Mock) -> None:
        """Test the `__attrs_post_init__` method."""

        blueprint = mock.MagicMock()
        _InvokedObject(name="test", blueprint=blueprint)    # type: ignore[abstract]

        mocked_super.assert_called_once()

    def test_blender_object(self) -> None:
        """Test the property `blender_object`."""

        mt_blueprint = MeasurementTechniqueBlueprint(
            name="TestBlueprint",
            measurement_technique_prototype_name="secondary_electron_microscope",
            measurement_volume_material_prototype_name="vacuum")

        _InvokedObject._registry = MEASUREMENT_TECHNIQUE_REGISTRY    # type: ignore
        invoked_object = _InvokedObject(name=mt_blueprint.name,
                                        blueprint=mt_blueprint)    # type: ignore

        with mock.patch("synthpic2.recipe.blueprints.blueprints.get_object") as mocked:
            _ = invoked_object.blender_object
            mocked.assert_called_once_with(invoked_object.name)

    def test_update_feature_blender_links(self) -> None:
        """Test the method `update_feature_blender_links`."""

        mt_blueprint = MeasurementTechniqueBlueprint(
            name="TestBlueprint",
            measurement_technique_prototype_name="secondary_electron_microscope",
            measurement_volume_material_prototype_name="vacuum")

        _InvokedObject._registry = MEASUREMENT_TECHNIQUE_REGISTRY    # type: ignore
        invoked_object = _InvokedObject(name=mt_blueprint.name,
                                        blueprint=mt_blueprint)    # type: ignore

        # Mock the feature's method of the invoked objects
        for feat in invoked_object.features:
            feat.update_blender_link = mock.Mock()

        renaming_maps = {"dummy": {"renaming": "mapping"}}
        invoked_object.update_feature_blender_links(renaming_maps)
        for feat in invoked_object.features:
            feat.update_blender_link.assert_called_once_with(renaming_maps)
