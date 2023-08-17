"""Module for State handling steps."""

import attr
from omegaconf import MISSING

from ...registries import STATE_REGISTRY
from ..state import RuntimeState
from .base import FeatureGenerationStep


@attr.s(auto_attribs=True)
class LoadState(FeatureGenerationStep):
    """Synth chain step to load a previously saved state."""
    name: str = MISSING

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        state = STATE_REGISTRY[self.name]
        state.load_from_disk()

        return state.runtime_state
