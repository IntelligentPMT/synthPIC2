"""Prototype definitions."""

from abc import ABC
import os
from pathlib import Path
from typing import Dict, List, Optional

import attr
import bpy
from omegaconf import MISSING

from synthpic2.custom_types import RenamingMap
from synthpic2.recipe.render_preparation_mixin import RenderPreparationMixin

from ...blender.utilities import get_object, activate
from ...errors import ConventionError
from ...errors import PrototypeAlreadyExistsError
from ...errors import PrototypeNotFoundError
from ..registries import GEOMETRY_PROTOTYPE_REGISTRY
from ..registries import MATERIAL_PROTOTYPE_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY
from ..registries import Registry
from ..registries import SelfRegisteringAttrsMixin
from .feature import Feature


@attr.s(auto_attribs=True)
class _Prototype(SelfRegisteringAttrsMixin, ABC):
    """Basic prototype definition with attributes common to all other prototype
    classes."""

    blend_file_path: str = attr.field()
    name: str = MISSING

    features: Optional[List[Feature]] = None

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        if self.features is None:
            self.features = []

    @blend_file_path.validator    #type: ignore
    def validate_blend_file_path(self, _: attr.Attribute, value: str) -> None:
        blend_file_path = Path(value).resolve()

        if not blend_file_path.exists():
            raise FileNotFoundError(f"Blend file not found: {blend_file_path}")

        self.blend_file_path = str(blend_file_path)


@attr.s(auto_attribs=True)
class MeasurementTechniquePrototype(_Prototype, RenderPreparationMixin):
    """Prototype definition for a measurement technique."""
    _target_: str = "synthpic2.recipe.prototypes.MeasurementTechniquePrototype"
    measurement_volume_object_name: str = "MeasurementVolume"
    background_object_name: Optional[str] = None
    hideable_object_names: Optional[List[str]] = None

    @property
    def _registry(self) -> Registry:
        return MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self._add_render_features()

        if self.hideable_object_names is None:
            self.hideable_object_names = []

        if self.background_object_name is not None:
            self.hideable_object_names.append(self.background_object_name)

        self.hideable_object_names.append(self.measurement_volume_object_name)

    def _add_render_features(self) -> None:
        assert self.features is not None

        # Scene features
        blender_link_base_scene = "bpy.data.scenes['Scene']."

        self.features.append(
            Feature(name="cycles_samples",
                    blender_link=blender_link_base_scene + "cycles.samples"))

        # Render features
        # TODO: Consider iterating `bpy.data.scenes['Scene'].render`, to give an
        # interface to all render settings.

        blender_link_base_render = blender_link_base_scene + "render."

        render_feature_names = [
            "resolution_x",
            "resolution_y",
            "resolution_percentage",
        ]

        for render_feature_name in render_feature_names:
            self.features.append(
                Feature(name=render_feature_name,
                        blender_link=blender_link_base_render + render_feature_name))

        # Image features
        blender_link_base_image = blender_link_base_render + "image_settings."

        image_feature_names = [
            "color_mode",
            "color_depth",
            "compression",
        ]

        for image_feature_name in image_feature_names:
            self.features.append(
                Feature(name=image_feature_name,
                        blender_link=blender_link_base_image + image_feature_name))

    def initialize(self) -> None:
        """Open the blend file that is associated with the prototype."""
        bpy.ops.wm.read_homefile(use_factory_startup=True, use_empty=True)
        bpy.ops.outliner.orphans_purge(do_local_ids=True,
                                       do_linked_ids=True,
                                       do_recursive=True)

        bpy.ops.wm.open_mainfile(filepath=self.blend_file_path)

        self._validate()
        self._fix_common_user_errors()

        #? Should we determine and store the collection of the measurement technique?

    def setup_after_invocation(self) -> None:
        """Setup steps to be executed after the `MeasurementTechniquePrototype` has been
        invoked as part of a `MeasurementTechniqueBlueprint`."""
        pass

    def _fix_common_user_errors(self) -> None:
        """Fix common user errors, such as no active object or measurement technique
        being in edit mode."""

        # If there is no active object, then activate the first object.
        if bpy.context.view_layer.objects.active is None:
            activate(bpy.data.objects[0])

        # Set object mode.
        if bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    # Not static, in case access to self is required later.
    def _validate(self) -> None:
        """Validate that the specified blend file sticks to the conventions of
        synthPIC2.

        Raises:
            ConventionError: if there is no scene named 'Scene' in the measurement
                technique prototype
            ConventionError: if there is no collection named 'MeasurementTechnique' in
                the measurement technique prototype
            ConventionError: if there is no camera in the measurement technique
                prototype
        """

        #? Should we have unique exceptions based on the ConventionError class?
        #  Then we could have all errors gathered in the synthpic2.errors module.
        if "Scene" not in bpy.data.scenes:
            raise ConventionError(
                "Expected there to be a scene named 'Scene' in the measurement "
                "technique prototype.")

        if "MeasurementTechnique" not in bpy.data.collections:
            raise ConventionError(
                "Expected there to be a collection named 'MeasurementTechnique' in the "
                "measurement technique prototype.")

        if len(bpy.data.cameras) < 1:
            raise ConventionError(
                "Expected there to be a camera in the measurement technique prototype.")

        if "MeasurementVolume" not in bpy.data.objects:
            raise ConventionError(
                "Expected there to be an object named 'MeasurementVolume' in the "
                "measurement technique prototype.")

    def _prepare_categorical_rendering_mode(self) -> None:
        self._hide_hideable_objects()

    def _hide_hideable_objects(self) -> None:
        assert self.hideable_object_names is not None
        for object_name in self.hideable_object_names:
            blender_object = get_object(object_name)
            blender_object.hide_render = True

    def _prepare_real_rendering_mode(self) -> None:
        pass

    def _prepare_stylized_rendering_mode(self) -> None:
        self._hide_hideable_objects()

    def _prepare_stylized_xray_rendering_mode(self) -> None:
        self._hide_hideable_objects()

    def _prepare_normal_map_rendering_mode(self) -> None:
        self._hide_hideable_objects()

    def _prepare_depth_map_rendering_mode(self) -> None:
        self._hide_hideable_objects()


@attr.s(auto_attribs=True)
class _AppendablePrototype(_Prototype):
    """Prototypes that can be appended using `bpy.ops.wm.append`."""

    # Can't start with _ to work with Hydra instantiation.
    name_in_blend_file: str = MISSING

    def __attrs_post_init__(self) -> None:
        """Define attributes that are not accessible via Hydra."""
        super().__attrs_post_init__()

        self._internal_directory: str = MISSING
        self._internal_module_name: str = MISSING

    def update_feature_blender_links(self, renaming_maps: Dict[str,
                                                               RenamingMap]) -> None:
        if self.features is not None:
            for feature in self.features:
                feature.update_blender_link(renaming_maps)

    def append(self) -> None:
        """Append the prototype to the current blend state.

        Raises:
            PrototypeNotFoundError: if desired prototype does not exist in blend file
            PrototypeAlreadyExistsError: if prototype already exists in scene
        """
        if self.name_in_blend_file in self._internal_module:
            raise PrototypeAlreadyExistsError(prototype_name=self.name_in_blend_file)

        # Check if object/material with same name already exists.
        if self.name in self._internal_module:
            return

        directory = os.path.join(self.blend_file_path, self._internal_directory)
        try:
            bpy.ops.wm.append(directory=directory,
                              filename=self.name_in_blend_file,
                              set_fake=True)
        except RuntimeError as exception:
            if "cannot use current file as library" in exception.args[0]:
                raise PrototypeNotFoundError(self.blend_file_path,
                                             self.name_in_blend_file) from exception
            else:
                raise exception

        # Check if object/material was appended.
        if self.name_in_blend_file not in self._internal_module:
            raise PrototypeNotFoundError(self.blend_file_path, self.name_in_blend_file)

        self._internal_module.get(self.name_in_blend_file).name = self.name

        renaming_maps = {self._internal_directory: {self.name_in_blend_file: self.name}}
        self.update_feature_blender_links(renaming_maps)

    @property
    def _internal_module(self) -> bpy.types.Collection:
        return getattr(bpy.data, self._internal_module_name)

    @property
    def blender_object(self) -> bpy.types.Collection:
        return self._internal_module.get(self.name)


@attr.s(auto_attribs=True)
class GeometryPrototype(_AppendablePrototype):
    """Prototype for particle geometry."""
    _target_: str = "synthpic2.recipe.prototypes.GeometryPrototype"
    name_in_blend_file: str = "GeometryPrototype"

    @property
    def _registry(self) -> Registry:
        return GEOMETRY_PROTOTYPE_REGISTRY

    def __attrs_post_init__(self) -> None:
        """Define attributes that are not accessible via Hydra."""
        super().__attrs_post_init__()

        self._internal_directory = "Object"
        self._internal_module_name = "objects"
        self._particle_prototype_collection_name = "GeometryPrototypes"

    def append(self) -> None:
        """Append a GeometryPrototype, store it in the 'GeometryPrototypes' collection
        and hide said collection. """

        # Get "GeometryPrototypes" collection or create if necessary.
        collections = bpy.data.collections

        if self._particle_prototype_collection_name in collections:
            collection = collections[self._particle_prototype_collection_name]
        else:
            collection = collections.new(self._particle_prototype_collection_name)
            scene = bpy.data.scenes["Scene"]
            scene.collection.children.link(collection)

        # Hide collection in renders.
        view_layer = bpy.context.view_layer
        layer_collection = view_layer.layer_collection.children[collection.name]
        collection.hide_render = True

        # Activate "ParticlePrototypes" collection.
        view_layer.active_layer_collection = layer_collection

        super().append()


@attr.s(auto_attribs=True)
class MaterialPrototype(_AppendablePrototype):
    """Prototype definition for a material."""
    _target_: str = "synthpic2.recipe.prototypes.MaterialPrototype"
    name_in_blend_file: str = "MaterialPrototype"

    @property
    def _registry(self) -> Registry:
        return MATERIAL_PROTOTYPE_REGISTRY

    def __attrs_post_init__(self) -> None:
        """Define attributes that are not accessible via Hydra."""
        super().__attrs_post_init__()

        self._internal_directory = "Material"
        self._internal_module_name = "materials"
