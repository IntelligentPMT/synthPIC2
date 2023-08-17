"""Tests of the Registry class."""

from dataclasses import dataclass
import unittest

from synthpic2.errors import ConventionError
from synthpic2.recipe.registries.registry import Registry


@dataclass
class _ItemClass1:
    name: str


# @dataclass
# class _ItemClass2:
#     name: str


@dataclass
class _NoNameItemClass:
    pass


class TestRegistry(unittest.TestCase):
    """Tests of the Registry class."""

    def test_register_and_query_items(self) -> None:
        test_item1 = _ItemClass1(name="test_item")
        test_item2 = _ItemClass1(name="test_item2")

        registry = Registry()
        registry.register(test_item1)
        registry.register(test_item2)

        self.assertEqual(len(registry), 2)

        self.assertEqual([item.name for item in registry],
                         [test_item1.name, test_item2.name])

        self.assertIsNone(registry.query("non existent name"))
        with self.assertRaises(KeyError):
            registry.query("non existent name", strict=True)
        self.assertEqual(registry.query(test_item1.name), test_item1)
        self.assertEqual(registry.query(test_item2.name), test_item2)

        self.assertIsNone(registry.query(42))
        with self.assertRaises(KeyError):
            registry.query(42, strict=True)
        self.assertEqual(registry.query(0), test_item1)
        self.assertEqual(registry.query(1), test_item2)

        self.assertIsNone(registry["non existent name"])
        self.assertEqual(registry[test_item1.name], test_item1)
        self.assertEqual(registry[test_item2.name], test_item2)

        self.assertIsNone(registry[42])
        self.assertEqual(registry[0], test_item1)
        self.assertEqual(registry[1], test_item2)

    def test_register_item_without_name(self) -> None:
        test_item = _NoNameItemClass()

        registry = Registry()
        with self.assertRaises(AttributeError):
            registry.register(test_item)

    def test_register_duplicate_name(self) -> None:
        test_item1 = _ItemClass1(name="test_item")
        test_item2 = _ItemClass1(name="test_item")

        registry = Registry()
        registry.register(test_item1)

        with self.assertRaises(ConventionError):
            registry.register(test_item2)

    # def test_register_mixed_types(self) -> None:
    #     test_item1 = _ItemClass1(name="test_item")
    #     test_item2 = _ItemClass2(name="test_item2")

    #     registry = Registry()
    #     registry.register(test_item1)

    #     with self.assertRaises(TypeError):
    #         registry.register(test_item2)

    def test_clear(self) -> None:
        test_item1 = _ItemClass1(name="test_item")

        registry = Registry()
        registry.register(test_item1)

        registry.clear()

        self.assertEqual(len(registry), 0)

    def test_delete_item(self) -> None:
        test_item1 = _ItemClass1(name="test_item1")
        test_item2 = _ItemClass1(name="test_item2")
        test_item3 = _ItemClass1(name="test_item3")

        registry = Registry()
        registry.register(test_item1)
        registry.register(test_item2)
        registry.register(test_item3)

        registry.delete_item("test_item3")

        self.assertEqual(len(registry), 2)
        self.assertNotIn(test_item3, registry)

        registry.delete_item(0)

        self.assertEqual(len(registry), 1)
        self.assertNotIn(test_item1, registry)

        # Removal of non-existent items should not result in an exception.
        registry.delete_item("test_item3")
        registry.delete_item(3)
