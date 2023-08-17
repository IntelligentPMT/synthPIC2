"""Tests for the FeatureVariability class."""

import unittest
from unittest import mock

import bpy

from synthpic2.recipe.blueprints.blueprints import MeasurementTechnique
from synthpic2.recipe.blueprints.blueprints import \
    MeasurementTechniqueBlueprint
from synthpic2.recipe.blueprints.blueprints import Particle
from synthpic2.recipe.blueprints.blueprints import ParticleBlueprint
from synthpic2.recipe.process_conditions.feature_criteria import _IsType
from synthpic2.recipe.process_conditions.feature_criteria import ContainsString
from synthpic2.recipe.process_conditions.feature_criteria import \
    FeatureCriterion
from synthpic2.recipe.process_conditions.feature_criteria import IsEqualTo
from synthpic2.recipe.process_conditions.feature_criteria import IsGreaterThan
from synthpic2.recipe.process_conditions.feature_criteria import IsSmallerThan
from synthpic2.recipe.prototypes.feature import Feature
from synthpic2.recipe.registries import Registry
from synthpic2.recipe.registries.registries import CRITERION_REGISTRY


class _TestFeatureCriterionBase(unittest.TestCase):
    """Base class for tests of FeatureCriterion subclass."""

    def setUp(self) -> None:
        bpy.ops.wm.read_factory_settings()
        self.integer_feature = Feature(
            name="z_location", blender_link="bpy.data.objects['Cube'].location.z")
        self.string_feature = Feature(name="object_name",
                                      blender_link="bpy.data.objects['Cube'].name")
        self.feature_owner = mock.Mock()
        self.feature_owner.features = Registry("Feature")
        self.feature_owner.features.register(self.integer_feature)
        self.feature_owner.features.register(self.string_feature)


class _IncompatibleFeatureCriterion(FeatureCriterion):

    def check(self, feature: Feature) -> bool:
        raise TypeError


class TestFeatureCriterion(_TestFeatureCriterionBase):
    """Tests for FeatureCriterion class."""

    def test_call_nonexistent_features(self) -> None:
        """Test call method for non-existent features."""

        for default_return_value in (True, False):
            criterion = _IncompatibleFeatureCriterion(
                name="FeatureCriterion",
                feature_name="NonExistentFeature",
                default_return_value=default_return_value)
            self.assertEqual(criterion(self.feature_owner), default_return_value)
            CRITERION_REGISTRY.delete_item(index=criterion.name)

    def test_call_wrong_type(self) -> None:
        """Test call method resulting in a type error."""

        for default_return_value in (True, False):
            criterion = _IncompatibleFeatureCriterion(
                name="FeatureComparisonCriterion",
                feature_name=self.integer_feature.name,
                default_return_value=default_return_value)
            self.assertEqual(criterion(self.feature_owner), default_return_value)
            CRITERION_REGISTRY.delete_item(index=criterion.name)


class TestIsEqualToCriterion(_TestFeatureCriterionBase):
    """Tests for IsEqualTo class."""

    def test_call(self) -> None:
        """Test call method of the IsEqualTo criterion."""

        actual_feature_value = self.feature_owner.features["z_location"].value

        criterion = IsEqualTo(name="IsEqualToCriterion",
                              feature_name=self.integer_feature.name,
                              default_return_value=False,
                              comparand=actual_feature_value)
        self.assertTrue(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsEqualTo(name="IsEqualToCriterion",
                              feature_name=self.integer_feature.name,
                              default_return_value=False,
                              comparand=actual_feature_value + 1)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsEqualTo(name="IsEqualToCriterion",
                              feature_name=self.integer_feature.name,
                              default_return_value=False,
                              comparand=actual_feature_value - 1)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)


class TestIsGreaterThanCriterion(_TestFeatureCriterionBase):
    """Tests for IsGreaterThan class."""

    def test_call(self) -> None:
        """Test call method of the IsGreaterThan criterion."""

        actual_feature_value = self.feature_owner.features["z_location"].value

        criterion = IsGreaterThan(name="IsGreaterThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value - 1)
        self.assertTrue(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsGreaterThan(name="IsGreaterThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value + 1)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsGreaterThan(name="IsGreaterThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)


class TestIsSmallerThanCriterion(_TestFeatureCriterionBase):
    """Tests for IsSmallerThan class."""

    def test_call(self) -> None:
        """Test call method of the IsSmallerThan criterion."""

        actual_feature_value = self.feature_owner.features["z_location"].value

        criterion = IsSmallerThan(name="IsSmallerThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value + 1)
        self.assertTrue(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsSmallerThan(name="IsSmallerThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value - 1)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = IsSmallerThan(name="IsSmallerThanCriterion",
                                  feature_name=self.integer_feature.name,
                                  default_return_value=False,
                                  comparand=actual_feature_value)
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)


class TestContainsStringCriterion(_TestFeatureCriterionBase):
    """Tests for ContainsString class."""

    def test_call(self) -> None:
        """Test call method of the ContainsString criterion."""

        actual_feature_value = self.feature_owner.features["object_name"].value

        criterion = ContainsString(name="ContainsStringCriterion",
                                   feature_name=self.string_feature.name,
                                   default_return_value=False,
                                   search_string=actual_feature_value)
        self.assertTrue(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = ContainsString(name="ContainsStringCriterion",
                                   feature_name=self.string_feature.name,
                                   default_return_value=False,
                                   search_string=actual_feature_value[:-3])
        self.assertTrue(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)

        criterion = ContainsString(name="ContainsStringCriterion",
                                   feature_name=self.string_feature.name,
                                   default_return_value=False,
                                   search_string=actual_feature_value + "stuff")
        self.assertFalse(criterion(self.feature_owner))
        CRITERION_REGISTRY.delete_item(index=criterion.name)


class TestIsTypeCriterion(_TestFeatureCriterionBase):
    """Tests for _IsType class."""

    def test_call(self) -> None:
        """Test call method of the _IsType criterion."""

        with mock.patch("synthpic2.recipe.blueprints.blueprints.Particle",
                        autospec=True) as object_type:

            criterion = _IsType(name="IsType", type=Particle)
            self.assertTrue(criterion(object_type))
            CRITERION_REGISTRY.delete_item(index=criterion.name)

        with mock.patch("synthpic2.recipe.blueprints.blueprints.ParticleBlueprint",
                        autospec=True) as object_type:

            criterion = _IsType(name="IsType", type=ParticleBlueprint)
            self.assertTrue(criterion(object_type))
            CRITERION_REGISTRY.delete_item(index=criterion.name)

        with mock.patch("synthpic2.recipe.blueprints.blueprints.MeasurementTechnique",
                        autospec=True) as object_type:

            criterion = _IsType(name="IsType", type=MeasurementTechnique)
            self.assertTrue(criterion(object_type))
            CRITERION_REGISTRY.delete_item(index=criterion.name)

        with mock.patch(
                "synthpic2.recipe.blueprints.blueprints.MeasurementTechniqueBlueprint",
                autospec=True) as object_type:

            criterion = _IsType(name="IsType", type=MeasurementTechniqueBlueprint)
            self.assertTrue(criterion(object_type))
            CRITERION_REGISTRY.delete_item(index=criterion.name)
