"""Test the setup of the project."""

import importlib.machinery
import importlib.util
import unittest

import synthpic2


class UnittestSetUpTests(unittest.TestCase):
    """Sample tests for unittest setup."""

    def test_can_read_version(self) -> None:
        """Test can read the version string of the project."""

        version_string = synthpic2.__version__
        self.assertIsInstance(version_string, str)

    def test_bpy_module_is_installed(self) -> None:
        """Test that bpy module is correctly installed and can be imported."""

        bpy_module_spec = importlib.util.find_spec("bpy")
        self.assertIsInstance(bpy_module_spec, importlib.machinery.ModuleSpec)
