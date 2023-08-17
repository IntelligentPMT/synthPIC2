"""Tests for the prototype library."""

import unittest

from synthpic2 import PrototypeLibrary
from synthpic2.recipe.registries import GEOMETRY_PROTOTYPE_REGISTRY
from synthpic2.recipe.registries import MATERIAL_PROTOTYPE_REGISTRY
from synthpic2.recipe.registries import \
    MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY


class TestPrototypeLibrary(unittest.TestCase):
    """Tests of the ingredient library."""

    def test_load(self) -> None:
        """Test if the ingredient library can be loaded."""
        PrototypeLibrary.load()

        self.assertIn("sphere", GEOMETRY_PROTOTYPE_REGISTRY)
        self.assertIn("plain", MATERIAL_PROTOTYPE_REGISTRY)
        self.assertIn("secondary_electron_microscope",
                      MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY)
