"""Module for invocation synth chain steps."""

import attr

from ..state import RuntimeState
from .base import FeatureGenerationStep
from .set_based_mixin import SetBasedMixin


@attr.s(auto_attribs=True)
class InvokeBlueprints(SetBasedMixin, FeatureGenerationStep):
    """SynthChainStep to invoke a set of blueprints."""

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        for blueprint in self.affected_set():
            blueprint.invoke()

        return runtime_state
