"""Test the setup of the project."""

import os
import pathlib
from typing import List, Optional
import unittest

from hydra import compose
from hydra import initialize

from synthpic2 import execute_recipe

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()


class DemoRecipeTest(unittest.TestCase):
    """Execute all demo recipes."""
    recipe_root = "../recipes"
    output_root = PROJECT_ROOT / "output"

    def test_agglom_tem(self) -> None:
        self._test_recipe("agglom_tem")

    def test_beads(self) -> None:
        self._test_recipe("beads")

    def test_chocBeans_glassTable(self) -> None:    #pylint: disable=invalid-name
        self._test_recipe(
            "chocBeans_glassTable",
            overrides=[
                "process_conditions.feature_variabilities.CyclesSamples.variability.value=1",    #pylint: disable=line-too-long
                "blueprints.particles.Bead.number=1",
                "+synth_chain.feature_generation_steps.23.dry_run=False"
            ])

    def test_colPearls_plane(self) -> None:    #pylint: disable=invalid-name
        self._test_recipe("colPearls_plane")

    def test_secondary_electron_microscopy(self) -> None:
        self._test_recipe("spheres_sem",
                          overrides=[
                              "blueprints.particles.Bead.number=1",
                          ])

    def _test_recipe(self,
                     recipe_name: str,
                     overrides: Optional[List[str]] = None) -> None:
        """Execute a recipe to test it."""

        if overrides is None:
            overrides = []

        current_working_directory = pathlib.Path.cwd()
        output_folder = self.output_root / recipe_name
        output_folder.mkdir(exist_ok=True, parents=True)
        os.chdir(output_folder)

        try:
            with initialize(config_path=self.recipe_root):
                recipe = compose(config_name=recipe_name, overrides=overrides)
                execute_recipe(recipe)
        finally:
            os.chdir(current_working_directory)
