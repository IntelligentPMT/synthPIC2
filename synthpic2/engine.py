"""Engine to execute recipes."""

import logging
import os
from pathlib import Path
import sys

import hydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import OmegaConf
import wandb

# ! Workaround
# Blender messes with `sys.path`, which breaks pythons multiprocessing (see
# https://github.com/TylerGubala/blenderpy/issues/23#issuecomment-514826760).
# To fix this, we need to restore the original `sys.path`, after having imported the
# `bpy` module.

# pylint: disable=wrong-import-position

ORIGINAL_SYS_PATH = list(sys.path)

import bpy

sys.path = ORIGINAL_SYS_PATH

# ! ------------------------

from .prototype_library import PrototypeLibrary
from .recipe import Recipe
from .recipe import store as recipe_store
from .recipe.process_conditions.feature_criteria import \
    register_premade_feature_criteria
from .recipe.process_conditions.sets import register_premade_sets
from .recipe.registries import clear_all_registries
from .recipe.utilities import parse_recipe
from .utilities import get_hydra_output_root

recipe_store.populate()


def setup_run() -> None:
    setup_blender()
    PrototypeLibrary.load()
    register_premade_feature_criteria()
    register_premade_sets()


def setup_blender() -> None:
    bpy.context.preferences.edit.undo_steps = 0
    bpy.context.preferences.edit.undo_memory_limit = 1
    bpy.context.preferences.edit.use_global_undo = False


def clean_up_previous_run() -> None:
    clear_all_registries()

    bpy.ops.wm.read_factory_settings(use_empty=True)


@hydra.main(config_path=".", config_name="BaseRecipe")
def execute_recipe(recipe: Recipe) -> None:

    clean_up_previous_run()

    if "WANDB_API_KEY" in os.environ:
        wandb.init(
            project=HydraConfig.get().job.config_name,    #type: ignore
            group=Path(os.getcwd()).parent.name,
            config=OmegaConf.to_container(recipe, resolve=True),    # type: ignore
            settings=dict(start_method="thread"))

    logger = logging.getLogger("synthPIC2")
    logger.info("Starting run...")

    try:
        logger.info("Output root: %s", get_hydra_output_root())
    except ValueError:
        # If we are not running in Hydra (e.g. during tests), we can't get the output 
        # root.
        pass

    setup_run()
    parse_recipe(recipe)
    recipe_instantiated = hydra.utils.instantiate(recipe)
    recipe_instantiated.execute()

    logger.info("Finished run.\n")

    if wandb.run is not None:
        wandb.run.finish()
