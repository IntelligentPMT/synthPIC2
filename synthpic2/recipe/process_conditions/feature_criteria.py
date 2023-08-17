"""Home of Criterion classes to construct sets from."""

from abc import abstractmethod
from typing import Any, Type, Union

import attr
from omegaconf import MISSING

# from synthpic2.recipe.synth_chain.feature_generation_steps.set_based_mixin import SetBasedMixin

from ..blueprints.blueprints import MeasurementTechnique
from ..blueprints.blueprints import MeasurementTechniqueBlueprint
from ..blueprints.blueprints import Particle
from ..blueprints.blueprints import ParticleBlueprint
from ..prototypes.feature import Feature
from ..registries import CRITERION_REGISTRY
from ..registries import Registry
from ..registries.self_registering_attrs_mixin import SelfRegisteringAttrsMixin

FeatureOwner = Union[MeasurementTechniqueBlueprint, ParticleBlueprint,
                     MeasurementTechnique, Particle]


@attr.s(auto_attribs=True)
class BaseCriterion(SelfRegisteringAttrsMixin):
    name: str

    @property
    def _registry(self) -> Registry:
        return CRITERION_REGISTRY

    @abstractmethod
    def __call__(self, object_: FeatureOwner) -> bool:
        pass


@attr.s(auto_attribs=True)
class FeatureCriterion(BaseCriterion):
    """Criterion, to check if a certain `Feature` of an object has an
       `expected_value`.

    The `Feature` is looked up based on the specified `feature_name`. If the object
    does not have the `feature` at all, then the `default_return_value` will be
    returned.
    """

    feature_name: str
    default_return_value: bool
    _target_: str = "synthpic2.recipe.precess_conditions.criteria.FeatureCriterion"

    def __call__(self, object_: FeatureOwner) -> bool:

        feature = object_.features[self.feature_name]

        if feature is None:
            return self.default_return_value
        else:
            try:
                return self.check(feature)
            except TypeError:
                return self.default_return_value

    @abstractmethod
    def check(self, feature: Feature) -> bool:
        pass


@attr.s(auto_attribs=True)
class IsEqualTo(FeatureCriterion):
    comparand: Any = MISSING

    def check(self, feature: Feature) -> bool:
        return feature.value == self.comparand


@attr.s(auto_attribs=True)
class IsSmallerThan(FeatureCriterion):
    comparand: Any = MISSING

    def check(self, feature: Feature) -> bool:
        return feature.value < self.comparand


@attr.s(auto_attribs=True)
class IsGreaterThan(FeatureCriterion):
    comparand: Any = MISSING

    def check(self, feature: Feature) -> bool:
        return feature.value > self.comparand


@attr.s(auto_attribs=True)
class ContainsString(FeatureCriterion):
    search_string: str = MISSING

    def check(self, feature: Feature) -> bool:
        return self.search_string in feature.value


@attr.s(auto_attribs=True)
class _IsType(BaseCriterion):
    """Criterion, to check if an object is of a certain type."""
    type: Type

    def __call__(self, object_: FeatureOwner) -> bool:
        return isinstance(object_, self.type)


@attr.s(auto_attribs=True)
class AlwaysTrue(BaseCriterion):
    """Criterion that is always true."""
    name: str = "AlwaysTrue"

    def __call__(self, object_: FeatureOwner) -> bool:
        return True


@attr.s(auto_attribs=True)
class IsUltimateParent(BaseCriterion):
    """Criterion that is true, if the object is a particle and does not have a parent
    object."""
    name: str = "IsUltimateParent"

    def __call__(self, object_: FeatureOwner) -> bool:
        if not isinstance(object_, Particle):
            return False

        return object_.blender_object.parent is None


def register_premade_feature_criteria() -> None:
    _IsType(name="IsParticle", type=Particle)
    _IsType(name="IsParticleBlueprint", type=ParticleBlueprint)
    _IsType(name="IsMeasurementTechnique", type=MeasurementTechnique)
    _IsType(name="IsMeasurementTechniqueBlueprint", type=MeasurementTechniqueBlueprint)
    IsUltimateParent()
    AlwaysTrue()
