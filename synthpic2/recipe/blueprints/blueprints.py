"""Module for blueprints and helper classes."""

from abc import abstractmethod
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Union

import attr
import bpy
from omegaconf import MISSING

from synthpic2.recipe.prototypes.prototypes import MaterialPrototype

from ...blender.utilities import adapt_interface_iors
from ...blender.utilities import create_collection
from ...blender.utilities import duplicate_and_assign_material
from ...blender.utilities import duplicate_and_link_object
from ...blender.utilities import get_collection
from ...blender.utilities import get_object
from ...custom_types import RenamingMap
from ...utilities import get_object_md5
from ..prototypes import Feature
from ..registries import GEOMETRY_PROTOTYPE_REGISTRY
from ..registries import MATERIAL_PROTOTYPE_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_REGISTRY
from ..registries import PARTICLE_BLUEPRINT_REGISTRY
from ..registries import PARTICLE_REGISTRY
from ..registries import Registry
from ..registries import SelfRegisteringAttrsMixin

Features = List[Feature]


@attr.s(auto_attribs=True)
class _Blueprint(SelfRegisteringAttrsMixin):
    """Base class for Blueprints."""

    name: str
    custom_features: Optional[Features] = None

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()

        if self.custom_features is None:
            self.custom_features = []

        blueprint_name_feature = Feature(name="blueprint_name")
        blueprint_name_feature.value = self.name

        self.custom_features.append(blueprint_name_feature)

        self.features = Registry("Feature")

        for feature_subset in self._gather_feature_subsets():
            if feature_subset is not None:
                for feature in feature_subset:
                    self.features.register(feature)

    @abstractmethod
    def _gather_feature_subsets(self) -> List[Union[None, Features, Registry]]:
        pass

    @abstractmethod
    def invoke(self) -> None:
        pass


@attr.s(auto_attribs=True)
class ParticleBlueprint(_Blueprint):
    """Class to combine a `geometry_prototype` and a `material_prototype` to a
        particle."""
    _target_: str = "synthpic2.recipe.blueprints.ParticleBlueprint"
    geometry_prototype_name: str = MISSING
    material_prototype_name: str = "default"
    parent: str = "MeasurementVolume"
    number: int = MISSING

    @property
    def _registry(self) -> Registry:
        return PARTICLE_BLUEPRINT_REGISTRY

    def __attrs_post_init__(self) -> None:
        self.geometry_prototype = GEOMETRY_PROTOTYPE_REGISTRY.query(
            self.geometry_prototype_name, strict=True)

        self.material_prototype = MATERIAL_PROTOTYPE_REGISTRY.query(
            self.material_prototype_name, strict=True)

        super().__attrs_post_init__()

    def _gather_feature_subsets(self) -> List[Union[None, Features, Registry]]:
        return [
            self.custom_features, self.geometry_prototype.features,
            self.material_prototype.features
        ]

    def invoke(self) -> None:
        """Create the specified number of particles, according to the blueprint."""
        self.geometry_prototype.append()
        self.material_prototype.append()

        particle_collection_name = "Particles"
        if particle_collection_name not in bpy.data.collections:
            create_collection(collection_name=particle_collection_name,
                              scene=bpy.data.scenes[0])

        particle_collection = get_collection(particle_collection_name)

        for particle_id in range(self.number):

            suffix = self.name

            if particle_id > 0:
                suffix += f".{particle_id}"

            # Geometry
            geometry = self.geometry_prototype.blender_object
            blender_object, renaming_maps = duplicate_and_link_object(
                geometry, suffix, particle_collection)

            particle = Particle(name=blender_object.name, blueprint=self)
            particle.add_features(self.custom_features)
            particle.add_features(self.geometry_prototype.features)
            particle.update_feature_blender_links(renaming_maps)

            # Material
            renaming_maps = duplicate_and_assign_material(blender_object,
                                                          self.material_prototype.name,
                                                          suffix)
            particle.add_features(self.material_prototype.features)
            particle.update_feature_blender_links(renaming_maps)

            # TODO: We need to solve this more elegantly. E.g. replace
            #   "MeasurementVolume" with dynamic surrounding phase (it's not
            #   necessarily the parent). Generally, we need this to be less hard-coded.
            adapt_interface_iors(
                material_name_outside=get_object(
                    "MeasurementVolume").data.materials[0].name,
                material_name_inside=blender_object.data.materials[0].name)


@attr.s(auto_attribs=True)
class MeasurementTechniqueBlueprint(_Blueprint):
    """Class to combine a `measurement_technique_prototype` and a `material_prototype`
        to a particle."""
    _target_: str = "synthpic2.recipe.blueprints.MeasurementTechniqueBlueprint"
    measurement_technique_prototype_name: str = MISSING
    measurement_volume_material_prototype_name: str = "vacuum"
    background_material_prototype_name: str = "vacuum"

    # TODO: Add a compositing prototype (see
    # https://blender.stackexchange.com/questions/33576/how-do-you-import-a-compositing-node-set-up).

    name: str = "MeasurementTechnique"
    custom_features: Optional[Features] = None

    @property
    def _registry(self) -> Registry:
        return MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY

    def __attrs_post_init__(self) -> None:
        self.measurement_technique_prototype = \
        MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY.query(
            self.measurement_technique_prototype_name, strict=True)

        self.measurement_volume_material_prototype = MATERIAL_PROTOTYPE_REGISTRY.query(
            self.measurement_volume_material_prototype_name, strict=True)

        self.background_material_prototype = MATERIAL_PROTOTYPE_REGISTRY.query(
            self.background_material_prototype_name, strict=True)

        super().__attrs_post_init__()

    def _gather_feature_subsets(self) -> List[Union[None, Features, Registry]]:
        return [
            self.custom_features, self.measurement_technique_prototype.features,
            self.measurement_volume_material_prototype.features,
            self.background_material_prototype.features
        ]

    def invoke(self) -> None:
        """Load a `measurement_technique_prototype`, assign a
            `measurement_volume_material_prototype` and optionally assign a
            `background_material_prototype`."""
        self.measurement_technique_prototype.initialize()

        measurement_technique = MeasurementTechnique(name=self.name, blueprint=self)
        measurement_technique.add_features(
            self.measurement_technique_prototype.features)
        measurement_technique.add_features(self.custom_features)

        measurement_technique.assign_material_prototype_to_object(
            self.measurement_volume_material_prototype,
            self.measurement_technique_prototype.measurement_volume_object_name)

        if self.measurement_technique_prototype.background_object_name is not None:
            measurement_technique.assign_material_prototype_to_object(
                self.background_material_prototype,
                self.measurement_technique_prototype.background_object_name)

        self.measurement_technique_prototype.setup_after_invocation()


Blueprint = Union[ParticleBlueprint, MeasurementTechniqueBlueprint]


@attr.s(auto_attribs=True, eq=False)
class _InvokedObject(SelfRegisteringAttrsMixin):
    """Base class for objects, invoked by a blueprint."""
    name: str
    blueprint: Blueprint

    def __attrs_post_init__(self) -> None:
        SelfRegisteringAttrsMixin.__attrs_post_init__(self)
        self.features: Registry = Registry("Feature")

    @property
    def blender_object(self) -> bpy.types.Object:
        return get_object(self.name)

    def update_feature_blender_links(self, renaming_maps: Dict[str,
                                                               RenamingMap]) -> None:
        for feature in self.features:
            feature.update_blender_link(renaming_maps)

    def add_features(self, features: Optional[Iterable[Feature]]) -> None:
        if features is not None:
            for feature in features:
                self.features.register(deepcopy(feature))


class Particle(_InvokedObject):
    """Class to represent an object, invoked by a particle blueprint."""

    blueprint: ParticleBlueprint

    @property
    def _registry(self) -> Registry:
        return PARTICLE_REGISTRY

    @property
    def md5(self) -> str:
        relevant_blueprint_data = {
            "geometry_prototype_name": self.blueprint.geometry_prototype_name,
            "material_prototype_name": self.blueprint.material_prototype_name,
        }
        relevant_feature_data = {
            feature.name: feature.value for feature in self.features
        }

        relevant_data = {
            "blueprint": relevant_blueprint_data,
            "features": relevant_feature_data
        }

        return get_object_md5(relevant_data)


class MeasurementTechnique(_InvokedObject):
    """Class to store the features of a measurement technique."""

    blueprint: MeasurementTechniqueBlueprint

    @property
    def _registry(self) -> Registry:
        return MEASUREMENT_TECHNIQUE_REGISTRY

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()

        # Set default value for output root.
        if "output_root" not in self.features:
            self.features.register(Feature("output_root", _value=""))

    def prepare_for_render(self, rendering_mode: str) -> None:
        self.blueprint.measurement_technique_prototype.prepare_for_render(
            rendering_mode)

    def assign_material_prototype_to_object(self, material_prototype: MaterialPrototype,
                                            object_name: str) -> None:
        material_prototype.append()

        object_ = get_object(object_name)
        renaming_maps = duplicate_and_assign_material(object_,
                                                      material_prototype.name,
                                                      suffix=object_name)

        self.add_features(material_prototype.features)
        self.update_feature_blender_links(renaming_maps)
