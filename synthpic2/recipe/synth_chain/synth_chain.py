"""Module for the SynthChain class."""

import logging
from typing import List

import attr
from omegaconf import MISSING
from tqdm import tqdm
from wurlitzer import pipes
from wurlitzer import STDOUT

from ...utilities import seed_everything
from ..synth_chain.state import RuntimeState


@attr.s(auto_attribs=True)
class SynthChain:
    """Class to orchestrate the feature generation and the rendering."""
    # TODO: Add validation of `feature_generation_steps` and `rendering_steps`,
    #   preferably using Hydra.
    _target_: str = "synthpic2.recipe.SynthChain"
    blender_log_file_name: str = "blender.log"
    feature_generation_steps: List = MISSING
    rendering_steps: List = MISSING

    def execute(self, initial_runtime_state: RuntimeState) -> None:
        seed_everything(initial_runtime_state.seed)
        runtime_state = initial_runtime_state

        logger = logging.getLogger("synthPIC2")

        tqdm_bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}" \
            " [{elapsed}<{remaining}, {rate_inv_fmt}]"
        tqdm_unit = "step"

        logger.info("Feature generation...")
        for feature_generation_step in tqdm(self.feature_generation_steps,
                                            bar_format=tqdm_bar_format,
                                            unit=tqdm_unit):

            with open(self.blender_log_file_name, "a", encoding="utf-8") as log_file:
                with pipes(stdout=log_file, stderr=STDOUT):    #type: ignore
                    runtime_state = feature_generation_step(runtime_state)

        logger.info("Rendering...")
        for rendering_step in tqdm(self.rendering_steps,
                                   bar_format=tqdm_bar_format,
                                   unit=tqdm_unit):
            with open(self.blender_log_file_name, "a", encoding="utf-8") as log_file:
                with pipes(stdout=log_file, stderr=STDOUT):    #type: ignore
                    runtime_state = rendering_step(runtime_state)
