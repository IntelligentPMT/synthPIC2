"""Module that holds all the registries required by synthPIC2."""

from .measurement_technique_registry import MeasurementTechniqueRegistry
from .registry import Registry

MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY = Registry("MeasurementTechniquePrototype")
MATERIAL_PROTOTYPE_REGISTRY = Registry("MaterialPrototype")
GEOMETRY_PROTOTYPE_REGISTRY = Registry("GeometryPrototype")

PARTICLE_BLUEPRINT_REGISTRY = Registry("ParticleBlueprint")
MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY = Registry("MeasurementTechniqueBlueprint")

PARTICLE_REGISTRY = Registry("Particle")
MEASUREMENT_TECHNIQUE_REGISTRY = MeasurementTechniqueRegistry("MeasurementTechnique")

FEATURE_VARIABILITY_REGISTRY = Registry("FeatureVariability")
CRITERION_REGISTRY = Registry("Criterion")
SET_REGISTRY = Registry("Set")
STATE_REGISTRY = Registry("State")

REGISTRIES = [
    MEASUREMENT_TECHNIQUE_PROTOTYPE_REGISTRY,
    MATERIAL_PROTOTYPE_REGISTRY,
    GEOMETRY_PROTOTYPE_REGISTRY,
    PARTICLE_BLUEPRINT_REGISTRY,
    MEASUREMENT_TECHNIQUE_BLUEPRINT_REGISTRY,
    PARTICLE_REGISTRY,
    MEASUREMENT_TECHNIQUE_REGISTRY,
    FEATURE_VARIABILITY_REGISTRY,
    CRITERION_REGISTRY,
    SET_REGISTRY,
    STATE_REGISTRY,
]

def clear_all_registries() -> None:
    for registry in REGISTRIES:
        registry.clear()
