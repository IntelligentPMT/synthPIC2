"""Module for the TriggerFeatureUpdate class."""

import attr
from omegaconf import MISSING

from ...registries import FEATURE_VARIABILITY_REGISTRY
from ..state import RuntimeState
from .base import FeatureGenerationStep
from .set_based_mixin import SetBasedMixin


@attr.s(auto_attribs=True)
class TriggerFeatureUpdate(SetBasedMixin, FeatureGenerationStep):
    """SynthChainStep to update a feature of a set of objects according to a feature
        variability."""

    feature_variability_name: str = MISSING

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.feature_variability = FEATURE_VARIABILITY_REGISTRY.query(
            self.feature_variability_name, strict=True)

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        for object_ in self.affected_set():
            self.feature_variability.update_feature(object_)

        return runtime_state
