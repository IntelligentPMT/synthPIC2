"""Custom plugins for variabilities."""

import colorsys
import random
from typing import Any

import attr
import numpy as np
from omegaconf import MISSING

from synthpic2.recipe.process_conditions.variabilities import Variability


@attr.s(auto_attribs=True)
class ConstantHsvColorAsRgb(Variability):
    """Return a constant HSV color as RGB."""
    hue: float = 0.5
    saturation: float = 0.5
    value: float = 1
    alpha: float = 1

    def __attrs_post_init__(self) -> None:
        self._check_boundaries("hue")
        self._check_boundaries("saturation")
        self._check_boundaries("value")
        self._check_boundaries("alpha")

    def _check_boundaries(self, name: str) -> None:
        value = self.__getattribute__(name)

        if not 0 <= value <= 1:
            raise ValueError(f"Expected `{name}` to be >=0 and <=1, but got {value}.")

    def __call__(self) -> Any:

        return colorsys.hsv_to_rgb(self.hue, self.saturation,
                                   self.value) + (self.alpha,)


@attr.s(auto_attribs=True)
class RandomHsvColorAsRgb(Variability):
    """Return a random HSV color within certain boundaries as RGB."""
    h_min: float = 0
    h_max: float = 1

    s_min: float = 0
    s_max: float = 1

    v_min: float = 0
    v_max: float = 1

    alpha: float = 1

    def __attrs_post_init__(self) -> None:
        self._check_boundaries("h_min")
        self._check_boundaries("h_max")

        self._check_boundaries("s_min")
        self._check_boundaries("s_max")

        self._check_boundaries("v_min")
        self._check_boundaries("v_max")

        self._check_relation("h_min", "h_max")
        self._check_relation("s_min", "s_max")
        self._check_relation("v_min", "v_max")

        self._check_boundaries("alpha")

    def _check_boundaries(self, name: str) -> None:
        value = self.__getattribute__(name)

        if not 0 <= value <= 1:
            raise ValueError(f"Expected `{name}` to be >=0 and <=1, but got {value}.")

    def _check_relation(self, min_name: str, max_name: str) -> None:
        min_value = self.__getattribute__(min_name)
        max_value = self.__getattribute__(max_name)

        if not min_value <= max_value:
            raise ValueError(f"Expected `{min_name}` <= `{max_name}.`")

    def __call__(self) -> Any:
        h = random.uniform(self.h_min, self.h_max)
        s = random.uniform(self.s_min, self.s_max)
        v = random.uniform(self.v_min, self.v_max)

        return colorsys.hsv_to_rgb(h, s, v) + (self.alpha,)


@attr.s(auto_attribs=True)
class UniformDistributionInt(Variability):
    """Return a 1d uniform distribution."""
    location: int = MISSING
    scale: int = MISSING

    def __call__(self) -> int:
        r = self.location + np.random.randint(self.scale)

        return r


# @attr.s(auto_attribs=True)
# class LognormalDistribution3dHomogeneous(Variability):
#     # TODO: Implement.
#     pass

# @attr.s(auto_attribs=True)
# class WeibullDistribution3dHomogeneous(Variability):
#     # TODO: Implement.
#     pass
