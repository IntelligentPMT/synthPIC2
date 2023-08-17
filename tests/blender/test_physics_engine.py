"""Tests of Blender's physics engine (bullet)."""

import unittest

import bpy


class BlenderPhysicsEngineTest(unittest.TestCase):
    """Tests of Blender's physics engine (bullet)."""

    def test_engine_available(self) -> None:
        # Start with a clean scene.
        bpy.ops.wm.read_factory_settings()
        response = bpy.ops.rigidbody.object_add()

        self.assertTrue("FINISHED" in response)
