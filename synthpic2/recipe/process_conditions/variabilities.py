"""Module for the Variability class."""

from abc import ABC
from abc import abstractmethod
from typing import Any, Tuple

import attr
import numpy as np
from omegaconf import MISSING
from trimesh import sample as trimesh_sample

from ...blender.utilities import convert_blender_object_to_trimesh
from ...blender.utilities import get_object


# mypy ignore: see https://github.com/python/mypy/issues/5374
@attr.s(auto_attribs=True)
class Variability(ABC):
    """Variability class."""

    def __attrs_post_init__(self) -> None:
        self._parse_attributes()

    @abstractmethod
    def __call__(self) -> Any:
        pass

    def _parse_attributes(self) -> None:
        """Parse string attributes that include a set."""
        # TODO: Implement parsing (e.g.  using self.__dict__ and a regex).
        #   Check if a set/feature is being referenced (e.g. {self}.dimension,
        #   {all}.dimension).
        #   Reduce multiple values, e.g. average of feature values.

        # for key, value in self.__dict__:
        #     if isinstance(value, str):
        #         raise NotImplementedError


@attr.s(auto_attribs=True)
class UniformlyRandomLocationInMeasurementVolume(Variability):
    """Return a uniformly random coordinate location inside the MeasurementVolume."""

    def __call__(self) -> Tuple[float, float, float]:
        measurement_volume = get_object("MeasurementVolume")

        mesh = convert_blender_object_to_trimesh(measurement_volume)
        location = trimesh_sample.volume_mesh(mesh, count=1)[0]

        return location[0], location[1], location[2]


@attr.s(auto_attribs=True)
class UniformDistribution3dHomogeneous(Variability):
    """Return a uniform distribution of 3-tuples, each with identical elements."""
    location: float = MISSING
    scale: float = MISSING

    def __call__(self) -> tuple[float, float, float]:
        r = self.location + np.random.rand() * self.scale
        return (r,) * 3


@attr.s(auto_attribs=True)
class UniformDistributionNdHomogeneous(Variability):
    """Return a uniform distribution of n-tuples, each with identical elements. If n=1,
    returns a float."""
    location: float = MISSING
    scale: float = MISSING
    num_dimensions: int = 1

    def __call__(self) -> float | tuple[float, ...]:
        r = self.location + np.random.rand() * self.scale
        if self.num_dimensions == 1:
            return r
        else:
            return (r,) * self.num_dimensions


@attr.s(auto_attribs=True)
class LogNormal3dHomogeneous(Variability):
    """Return a log-normal distribution of 3-tuples, each with identical elements.

    # pylint: disable=line-too-long
    see https://numpy.org/doc/stable/reference/random/generated/numpy.random.lognormal.html

    mean = log(geometric_mean)
    sigma = log(geometric_standard_deviation)

    """
    geometric_mean: float = MISSING
    geometric_standard_deviation: float = MISSING
    min: float = -float("inf")
    max: float = float("inf")

    def __call__(self) -> Tuple[float, float, float]:
        while True:
            r = np.random.lognormal(
                np.log(self.geometric_mean),
                np.log(self.geometric_standard_deviation),
            )

            if self.min < r < self.max:
                break

        return (r,) * 3


@attr.s(auto_attribs=True)
class Constant(Variability):
    """Return a constant."""
    value: Any = MISSING

    def __call__(self) -> Any:
        return self.value
