"""Test cases for the built-in Variability classes."""

import unittest

import bpy
import numpy as np
from scipy.stats import gmean
from scipy.stats import gstd

from synthpic2.recipe.process_conditions.variabilities import \
    LogNormal3dHomogeneous
from synthpic2.recipe.process_conditions.variabilities import \
    UniformDistribution3dHomogeneous
from synthpic2.recipe.process_conditions.variabilities import \
    UniformlyRandomLocationInMeasurementVolume


class TestBaseVariability(unittest.TestCase):
    """Test cases for the internal class _Variability."""


class TestUniformlyRandomLocationInMeasurementVolume(unittest.TestCase):
    """Test cases for the class UniformlyRandomLocationInMeasurementVolume."""

    def test_call(self) -> None:
        """Test if returned values are valid."""
        np.random.seed(42)
        bpy.ops.wm.read_factory_settings()
        bpy.data.objects["Cube"].name = "MeasurementVolume"

        variability = UniformlyRandomLocationInMeasurementVolume()
        location = variability()

        self.assertEqual(location,
                         (-0.250919762305275, 0.9014286128198323, 0.4639878836228102))

        locations = []
        for _ in range(100):
            locations.append(variability())

        loc_array = np.array(locations)

        self.assertGreaterEqual(np.min(loc_array), -1)
        self.assertLessEqual(np.max(loc_array), 1)


class TestUniformDistribution3dHomogeneous(unittest.TestCase):
    """Test cases for the class UniformDistribution3dHomogeneous."""

    def test_call(self) -> None:
        """Test if returned values are valid."""
        np.random.seed(42)

        loc = 160e-6
        scale = 80e-6
        variability = UniformDistribution3dHomogeneous(location=loc, scale=scale)
        dimension = variability()

        self.assertTrue(all(dimension[0] == el for el in dimension[1:]))

        dimensions = []
        for _ in range(100):
            dimensions.append(variability())

        dim_array = np.array(dimensions)

        self.assertGreaterEqual(np.min(dim_array), loc)
        self.assertLessEqual(np.max(dim_array), loc + scale)


class TestLogNormalVariability(unittest.TestCase):
    """Test cases for the class LogNormalVariability."""

    def test_call(self) -> None:
        """Test if returned values are valid."""
        np.random.seed(42)

        geometric_mean = 100
        geometric_standard_deviation = 1.3
        variability = LogNormal3dHomogeneous(
            geometric_mean=geometric_mean,
            geometric_standard_deviation=geometric_standard_deviation)
        dimension = variability()

        self.assertTrue(all(dimension[0] == el for el in dimension[1:]))

        dimensions = []
        for _ in range(10000):
            dimensions.append(variability())

        dim_array = np.array(dimensions)

        self.assertAlmostEqual(gmean(dim_array.flatten()), geometric_mean, delta=0.1)
        self.assertAlmostEqual(gstd(dim_array.flatten()),
                               geometric_standard_deviation,
                               delta=0.002)

    def test_call_with_limits(self) -> None:
        """Test if returned values are valid."""
        np.random.seed(42)

        geometric_mean = 100
        geometric_standard_deviation = 1.3
        minimum = 99
        maximum = 101
        variability = LogNormal3dHomogeneous(
            geometric_mean=geometric_mean,
            geometric_standard_deviation=geometric_standard_deviation,
            min=minimum,
            max=maximum)

        dimensions = []
        for _ in range(10000):
            dimensions.append(variability())

        dim_array = np.array(dimensions)

        self.assertTrue((dim_array > minimum).all())
        self.assertTrue((dim_array < maximum).all())
