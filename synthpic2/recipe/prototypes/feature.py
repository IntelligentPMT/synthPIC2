"""Home of the Feature class."""

from dataclasses import dataclass
import re
from typing import Any, Dict, Literal, Optional

import bpy
# mathutils are only available after bpy module has been imported
from mathutils import Vector  # type: ignore
from omegaconf import MISSING

from ...blender.utilities import select_only
from ...custom_types import RenamingMap

__all__ = ["Feature"]

# TODO: Consider splitting Feature into BlenderFeature and NonBlenderFeature (e.g.
#   pressure). However, this makes it harder to work with structured configs, since they
#   don't support type unions.
# TODO: Add WrappedBlenderFeature, which allows easy conversion of values from and to
#   BlenderFeatures (e.g. RgbToHsv).
# TODO: Store NonBlender features also in blender, so that they are saved in the blender
#   state.

InterfaceType = Literal["dictionary", "list/tuple", "attribute"]
KeyType = str | int

@dataclass
class Feature:
    """This class allows to get and set feature values. These features can either be
    custom-defined, or link to a property of a Blender object.
    """
    name: str = MISSING
    blender_link: Optional[str] = None
    _target_: Optional[str] = "synthpic2.recipe.prototypes.Feature"
    _value: Optional[Any] = None

    def __post_init__(self) -> None:
        """Gets called after the init routine."""

        if not (self.blender_link is None or self._value is None):
            raise ValueError(
                "Expected either `blender_link` or `_value_` to be `None`.")

        if self.blender_link is not None:
            self._validate_blender_link()
            self._sanitize_blender_link()

    def _validate_blender_link(self) -> None:
        """Validate the `blender_link` property.

        Raises:
            ValueError: raised if the `blender_link` property is invalid
        """
        assert isinstance(self.blender_link, str)

        if not self.blender_link.startswith("bpy.data."):
            raise ValueError(f"Expected blender_link to start with 'bpy.data.'. Got "
                             f"'{self.blender_link}' instead.")

    def _sanitize_blender_link(self) -> None:
        """Sanitize the `blender_link` property."""
        if self.blender_link is not None:
            self.blender_link = self.blender_link.replace("'", '"')

    def _parse_blender_link(self) -> tuple[Any, InterfaceType, KeyType]:
        """Extract the attributes from blender_link and assign it to value.

        https://regex101.com/r/k5ClC9/1
        """

        assert isinstance(self.blender_link, str)

        #  Matches `.abc` or `["abc"]` or `[123]`
        regex = r"(?:\.(\w+))|(?:\[\"([^\"]+)\"\])|(?:\[(\d+)])"

        matches = list(re.finditer(regex, self.blender_link))

        parent_node = bpy

        for match in matches[:-1]:
            interface, key = self._parse_node_interface_and_key(match)

            parent_node = self._get_node_value(parent_node, interface, key)

        final_node = parent_node

        # Check, what data type the final node belongs to (attribute, dictionary or
        # list/tuple).
        final_match = matches[-1]
        final_interface, final_key = \
            self._parse_node_interface_and_key(final_match)

        return final_node, final_interface, final_key

    @staticmethod
    def _get_node_value(node: Any, interface: InterfaceType, key: KeyType) -> Any:
        match interface:
            case "list/tuple" | "dictionary":
                node = node.__getitem__(key)
            case "attribute":
                assert isinstance(key, str)
                node = getattr(node, key)
            case _:
                raise KeyError(f"Could not get value for: {node}")
        return node

    @staticmethod
    def _set_node_value(node: Any,
                        interface: InterfaceType,
                        key: KeyType,
                        value: Any) -> None:
        match interface:
            case "list/tuple" | "dictionary":
                node.__setitem__(key, value)
            case "attribute":
                assert isinstance(key, str)
                setattr(node, key, value)

    @staticmethod
    def _parse_node_interface_and_key(regex_match: re.Match) \
        -> tuple[InterfaceType, int | str]:
        match regex_match.groups():
            case (None, None, key):
                key = int(key)
                interface: InterfaceType = "list/tuple"
            case (None, key, None):
                interface = "dictionary"
            case (key, None, None):
                interface = "attribute"
            case _:
                raise ValueError("Could not parse `blender_link`.")

        return interface, key

    @property
    def value(self) -> Any:
        if self.blender_link is None:
            return self._value
        else:
            node, interface, key = self._parse_blender_link()

            v = self._get_node_value(node, interface, key)

            if isinstance(v, Vector):
                v = tuple(v)

            return v

    @value.setter
    def value(self, value: Any) -> None:
        if self.blender_link is None:
            self._value = value
        else:
            node, interface, key = self._parse_blender_link()
            # assert isinstance(key, str)

            self._set_node_value(node, interface, key, value)

            if key == "dimensions" and interface=="attribute":
                select_only(node)
                bpy.ops.object.transform_apply(location=False,
                                               rotation=False,
                                               scale=True)

        # TODO: Incorporate more meaningful error messages like in
        #   https://github.com/maxfrei750/synthPIC2/blob/8005477f1d755fe7fbaee10758bc18edb91c3320/synthpic2/blender/utilities.py#L30 #pylint: disable=line-too-long

    def update_blender_link(self, renaming_maps: Dict[str, RenamingMap]) -> None:

        if self.blender_link is None:
            return

        blender_module_map = {
            "Object": "objects",
            "Mesh": "meshes",
            "Material": "materials",
            "Particle Settings": "particles",
            "Geometry Node Tree": "node_groups",
            "Texture": "textures",
            "MetaBall": "metaballs",
        }

        blender_link_root = "bpy.data."

        for data_block_type, renaming_map in renaming_maps.items():
            if data_block_type not in blender_module_map:
                raise ValueError(f"Unsupported data block type: {data_block_type}")

            blender_module_name = blender_module_map[data_block_type]

            for old_name, new_name in renaming_map.items():
                search_term = f'{blender_link_root}{blender_module_name}["{old_name}"].'
                replace_term = f'{blender_link_root}{blender_module_name}["{new_name}"].'

                self.blender_link = self.blender_link.replace(search_term, replace_term)
