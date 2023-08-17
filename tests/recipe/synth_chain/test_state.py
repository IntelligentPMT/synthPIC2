"""Tests for the State class."""

from copy import deepcopy
import unittest

import bpy
import yaml

from synthpic2.blender.utilities import select_only
from synthpic2.recipe.synth_chain.state import RuntimeState
from synthpic2.recipe.synth_chain.state import State


class TestState(unittest.TestCase):
    """Tests of the State class."""

    # pylint: disable=protected-access

    def test_save_load_methods(self) -> None:
        """Test the methods `save_to_disk` and `load_from_disk`."""

        bpy.ops.wm.read_factory_settings()

        runtime_state = RuntimeState(time=0, seed=123)
        state = State(name="test_state", runtime_state=runtime_state)

        # Test the save_to_disk method
        state.save_to_disk()

        self.assertTrue(state._blend_file_path.exists())
        self.assertTrue(state._runtime_state_file_path.exists())

        with open(state._runtime_state_file_path, "r", encoding="utf-8") as yaml_file:
            loaded_runtime_state = yaml.load(yaml_file, Loader=yaml.Loader)

        self.assertEqual(runtime_state, loaded_runtime_state)

        # Test the load_from_disk method
        select_only(bpy.data.objects["Cube"])
        bpy.ops.object.delete()

        with self.assertRaises(KeyError):
            _ = bpy.data.objects["Cube"]

        original_state = deepcopy(state)
        state.runtime_state.time = 1000

        state.load_from_disk()

        self.assertIsNotNone(bpy.data.objects["Cube"])
        self.assertEqual(state, original_state)
