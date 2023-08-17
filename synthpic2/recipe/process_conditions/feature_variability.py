"""Module for the FeatureVariability class."""

from typing import Any, Union

import attr
from omegaconf import MISSING

from ..blueprints import MeasurementTechnique
from ..blueprints import Particle
from ..registries.registries import FEATURE_VARIABILITY_REGISTRY
from ..registries.registries import Registry
from ..registries.self_registering_attrs_mixin import SelfRegisteringAttrsMixin


@attr.s(auto_attribs=True)
class FeatureVariability(SelfRegisteringAttrsMixin):
    """Class to combine a feature (specified by its name) with a Variability."""
    _target_: str = "synthpic2.recipe.process_conditions.feature_variability.FeatureVariability"    #pylint: disable=line-too-long
    name: str = MISSING
    feature_name: str = MISSING
    variability: Any = MISSING

    @property
    def _registry(self) -> Registry:
        return FEATURE_VARIABILITY_REGISTRY

    # TODO: Add validation for `variability` (previously, check if hydra can do this
    # for us). See:
    # https://stackoverflow.com/questions/50817332/python-attrs-package-validators-after-instantiation

    def update_feature(self, object_: Union[Particle, MeasurementTechnique]) -> None:
        feature = object_.features[self.feature_name]

        if feature is not None:
            # TODO?: Pass the object to the variability, so that one feature can depend
            #   on another feature.
            feature.value = self.variability()    #pylint: disable=not-callable

            # TODO?: If the object has children, update their features as well?
