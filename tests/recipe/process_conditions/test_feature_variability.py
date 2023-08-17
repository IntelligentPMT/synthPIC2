"""Tests for the FeatureVariability class."""

import unittest
from unittest import mock

import bpy
import numpy as np

from synthpic2.recipe.process_conditions.feature_variability import \
    FeatureVariability
from synthpic2.recipe.process_conditions.variabilities import \
    UniformDistribution3dHomogeneous
from synthpic2.recipe.prototypes.feature import Feature
from synthpic2.recipe.registries import Registry


class TestFeatureVariability(unittest.TestCase):
    """Test the FeatureVariability class."""

    def test_attrs_class(self) -> None:
        with mock.patch(
                "synthpic2.recipe.process_conditions.feature_variability." \
                    "FeatureVariability.__attrs_post_init__"
        ) as mocked_method:
            _ = FeatureVariability(name="test",
                                   feature_name="b",
                                   variability=mock.Mock())
            mocked_method.assert_called_once()

    def test_update_feature(self) -> None:
        """Test the update_feature method."""
        feature_name = "dimensions"
        expected_feature_value = 160e-6

        # Test vary dimension
        bpy.ops.wm.read_factory_settings()
        particle = mock.Mock()
        particle.features = Registry("Feature")
        particle.features.register(
            Feature(name=feature_name,
                    blender_link="bpy.data.objects['Cube'].dimensions"))

        variability = UniformDistribution3dHomogeneous(location=expected_feature_value,
                                                       scale=0)
        feature_variability = FeatureVariability(name="CubeDimension",
                                                 feature_name=feature_name,
                                                 variability=variability)

        feature_variability.update_feature(particle)

        np.testing.assert_allclose(tuple(particle.features[feature_name].value),
                                   (expected_feature_value,) * 3)
