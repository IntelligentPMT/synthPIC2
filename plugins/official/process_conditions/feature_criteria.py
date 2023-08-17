"""Custom plugins for feature criteria."""

import colorsys
from typing import Any

import attr
from omegaconf import MISSING

from synthpic2.recipe.process_conditions.feature_criteria import \
    FeatureCriterion
from synthpic2.recipe.prototypes.feature import Feature


@attr.s(auto_attribs=True)
class InCompartment(FeatureCriterion):
    """Returns True if feature.value is in specified compartment_no for a total of compartments_total every repeating interval of interval_length units"""
    compartment_no: Any = MISSING
    compartments_total: Any = MISSING
    interval_length: float = 1

    def check(self, feature: Feature) -> bool:
        category_min = self.interval_length / self.compartments_total * (self.compartment_no - 1)
        category_max = self.interval_length / self.compartments_total * (self.compartment_no)
        return ((feature.value % self.interval_length) >= category_min) and (
            (feature.value % self.interval_length) < category_max)


@attr.s(auto_attribs=True)
class InHsvRange(FeatureCriterion):
    """Returns True if the checked HSV values are within hsv_min <= hsv < hsv_max."""
    h_min: float = 0
    h_max: float = 1

    s_min: float = 0
    s_max: float = 1

    v_min: float = 0
    v_max: float = 1

    def check(self, feature: Feature) -> bool:
        h, s, v = colorsys.rgb_to_hsv(feature.value[0], feature.value[1],
                                      feature.value[2])
        condition_h = (h >= self.h_min and h < self.h_max)
        condition_s = (s >= self.s_min and s < self.s_max)
        condition_v = (v >= self.v_min and v < self.v_max)

        return condition_h and condition_s and condition_v
