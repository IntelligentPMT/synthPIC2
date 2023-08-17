"""Module for State handling steps."""

from pathlib import Path
from typing import Optional

import attr

from ...registries import MEASUREMENT_TECHNIQUE_REGISTRY
from ..state import RuntimeState
from ..state import State
from .rendering import ParametricRenderingStep


@attr.s(auto_attribs=True)
class SaveState(ParametricRenderingStep):
    """Synth chain step to save a state to disk."""
    name: Optional[str] = None

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        # Use the fact, that there is only a single measurement technique.
        measurement_technique = MEASUREMENT_TECHNIQUE_REGISTRY[0]

        self.output_root = Path(measurement_technique.features["output_root"].value)

        state = State(name=self.name,
                      runtime_state=runtime_state,
                      file_root=self.output_root)
        state.save_to_disk()

        return state.runtime_state
