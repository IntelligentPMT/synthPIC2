"""Tests for the prototypes."""

from pathlib import Path
import unittest
from unittest.mock import patch

import bpy

from synthpic2.errors import ConventionError
from synthpic2.errors import PrototypeNotFoundError
from synthpic2.recipe.prototypes import GeometryPrototype
from synthpic2.recipe.prototypes import MaterialPrototype
from synthpic2.recipe.prototypes import MeasurementTechniquePrototype
from synthpic2.recipe.prototypes.prototypes import _Prototype


class BaseTestPrototype(unittest.TestCase):
    """Base test for *Prototype classes."""
    fixture_dir = Path.cwd() / "tests/fixtures"
    empty_blend_file = fixture_dir / "empty.blend"

    def setUp(self) -> None:
        super().setUp()
        bpy.ops.wm.read_factory_settings()


class TestMeasurementTechniquePrototype(BaseTestPrototype):
    """Tests of the MeasurementTechniquePrototype class."""

    def setUp(self) -> None:
        self.test_blend_file = self.fixture_dir / "secondary_electron_microscope.blend"

    def test_initialize(self) -> None:
        mt_prototype = MeasurementTechniquePrototype(name="test1",
                                                     blend_file_path=str(
                                                         self.test_blend_file))

        mt_prototype.initialize()

    def test_initialize_empty(self) -> None:
        # TODO: Write more tests to test validation of conventions.
        mt_prototype = MeasurementTechniquePrototype(name="test2",
                                                     blend_file_path=str(
                                                         self.empty_blend_file))

        with self.assertRaises(ConventionError):
            mt_prototype.initialize()


class TestPrototype(BaseTestPrototype):
    """Tests of the _Prototype base class."""

    # pylint: disable=abstract-class-instantiated

    @patch("synthpic2.recipe.prototypes.prototypes._Prototype.__abstractmethods__",
           set())
    def test_blend_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            _Prototype(
                blend_file_path="path/to/nowhere.blend")    # type: ignore[abstract]


class TestAppendablePrototype(BaseTestPrototype):
    """Tests of the _AppendablePrototype base class."""

    # TODO: Test for PrototypeAlreadyExistsError.


class TestMaterialPrototype(BaseTestPrototype):
    """Tests of the MaterialPrototype class."""

    def setUp(self) -> None:
        self.test_blend_file = self.fixture_dir / "plain.blend"

    def test_append(self) -> None:

        new_name = "plain"

        # yapf: disable
        material_prototype = MaterialPrototype(
            blend_file_path=str(self.test_blend_file),
            name=new_name,
        )
        # yapf: enable

        material_prototype.append()

        new_material = bpy.data.materials[new_name]
        self.assertEqual(new_material.name, new_name)

    def test_append_empty(self) -> None:
        material_prototype = MaterialPrototype(
            blend_file_path=str(self.empty_blend_file),
            name="Test",
        )

        with self.assertRaises(PrototypeNotFoundError):
            material_prototype.append()


class TestParticlePrototype(BaseTestPrototype):
    """Tests of the ParticlePrototype class."""

    def setUp(self) -> None:
        self.test_blend_file = self.fixture_dir / "sphere.blend"

    def test_append(self) -> None:

        num_prototypes = 3

        for prototype_id in range(num_prototypes):
            new_name = f"Prototype{prototype_id}"

            particle_prototype = GeometryPrototype(
                blend_file_path=str(self.test_blend_file),
                name=new_name,
            )

            particle_prototype.append()

            # Check that renaming worked.
            new_object = bpy.data.objects[new_name]
            self.assertEqual(new_object.name, new_name)

            # Check that prototype was moved to 'GeometryPrototypes' collection.
            particle_prototype_collection = bpy.data.collections["GeometryPrototypes"]
            self.assertTrue(new_name in particle_prototype_collection.all_objects)

            # Check that 'GeometryPrototypes' collection is hidden in renders.
            self.assertTrue(particle_prototype_collection.hide_render)

    def test_append_empty(self) -> None:
        particle_prototype = GeometryPrototype(
            blend_file_path=str(self.empty_blend_file),
            name="Test",
        )

        with self.assertRaises(PrototypeNotFoundError):
            particle_prototype.append()
