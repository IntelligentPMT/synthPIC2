"""Home of the Set class."""

import re
from typing import List, Union

import attr
from omegaconf import MISSING

from ...utilities import get_object_md5
from ..blueprints.blueprints import MeasurementTechnique
from ..blueprints.blueprints import MeasurementTechniqueBlueprint
from ..blueprints.blueprints import Particle
from ..blueprints.blueprints import ParticleBlueprint
from ..registries import CRITERION_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
from ..registries import MEASUREMENT_TECHNIQUE_REGISTRY
from ..registries import PARTICLE_BLUEPRINT_REGISTRY
from ..registries import PARTICLE_REGISTRY
from ..registries import SET_REGISTRY
from ..registries.registry import Registry
from ..registries.self_registering_attrs_mixin import SelfRegisteringAttrsMixin
from .boolean_expression_parsing import parse_boolean_string
from .feature_criteria import FeatureOwner

FeatureOwners = Union[List[MeasurementTechniqueBlueprint], List[ParticleBlueprint],
                      List[MeasurementTechnique], List[Particle]]


@attr.s(auto_attribs=True)
class Set(SelfRegisteringAttrsMixin):
    """Class to combine multiple FeatureCriterion instances."""
    name: str = MISSING
    criterion: str = "True"
    _target_: str = "synthpic2.recipe.process_conditions.sets.Set"
    _relevant_registries = [
        PARTICLE_REGISTRY, PARTICLE_BLUEPRINT_REGISTRY, MEASUREMENT_TECHNIQUE_REGISTRY,
        MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY
    ]

    @property
    def _registry(self) -> Registry:
        return SET_REGISTRY

    def __attrs_post_init__(self) -> None:
        """Define attributes that are not accessible via Hydra."""
        super().__attrs_post_init__()
        self.parse_criterion()

    def parse_criterion(self) -> None:
        # Extract feature criteria.
        regex = r"\$(\w*)"
        matches = re.finditer(regex, self.criterion)

        self.parsing_map = {}

        for match in matches:
            feature_criterion_placeholder = match.group()
            feature_criterion_name = match.groups()[0]

            feature_criterion = CRITERION_REGISTRY[feature_criterion_name]

            if feature_criterion is None:
                raise ValueError(f"Could not parse set criterion `{self.criterion}`, "
                                 f"because there is no feature criterion with name "
                                 f"`{feature_criterion_name}`.")

            self.parsing_map[feature_criterion_placeholder] = feature_criterion

    def check_criterion(self, obj: FeatureOwner) -> bool:

        criterion = self.criterion

        for feature_criterion_placeholder, feature_criterion in self.parsing_map.items(
        ):

            criterion = criterion.replace(feature_criterion_placeholder,
                                          str(feature_criterion(obj)))

        return parse_boolean_string(criterion)

    def __call__(self) -> FeatureOwners:

        output_list: Union[FeatureOwners, List] = []

        for registry in self._relevant_registries:
            for obj in registry:
                if self.check_criterion(obj):
                    output_list.append(obj)

        return output_list

    @property
    def md5(self) -> str:
        items = self()
        if not all(isinstance(item, Particle) for item in items):
            raise RuntimeError(
                "Hashing is only supported for sets containing only particles.")

        particle_md5s = sorted([getattr(particle, "md5") for particle in items
                               ])    # `getattr` makes mypy happy.
        return get_object_md5(particle_md5s)


@attr.s(auto_attribs=True)
class AllParticlesSet(Set):
    _relevant_registries = [PARTICLE_REGISTRY]

    def __attrs_post_init__(self) -> None:
        self.name = "AllParticles"
        super().__attrs_post_init__()


@attr.s(auto_attribs=True)
class AllUltimateParentsSet(Set):
    _relevant_registries = [PARTICLE_REGISTRY]

    def __attrs_post_init__(self) -> None:
        self.name = "AllUltimateParents"
        self.criterion = "$IsUltimateParent"
        super().__attrs_post_init__()


@attr.s(auto_attribs=True)
class AllMeasurementTechniquesSet(Set):
    _relevant_registries = [MEASUREMENT_TECHNIQUE_REGISTRY]

    def __attrs_post_init__(self) -> None:
        self.name = "AllMeasurementTechniques"
        super().__attrs_post_init__()


@attr.s(auto_attribs=True)
class AllMeasurementTechniqueBlueprintsSet(Set):
    _relevant_registries = [MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY]

    def __attrs_post_init__(self) -> None:
        self.name = "AllMeasurementTechniqueBlueprints"
        super().__attrs_post_init__()


@attr.s(auto_attribs=True)
class AllParticleBlueprintsSet(Set):
    _relevant_registries = [PARTICLE_BLUEPRINT_REGISTRY]

    def __attrs_post_init__(self) -> None:
        self.name = "AllParticleBlueprints"
        super().__attrs_post_init__()


@attr.s(auto_attribs=True)
class EmptySet(Set):
    _relevant_registries: List[Registry] = []

    def __attrs_post_init__(self) -> None:
        self.name = "Empty"
        super().__attrs_post_init__()


def register_premade_sets() -> None:
    AllParticlesSet()
    AllMeasurementTechniquesSet()
    AllMeasurementTechniqueBlueprintsSet()
    AllParticleBlueprintsSet()
    EmptySet()
    AllUltimateParentsSet()
