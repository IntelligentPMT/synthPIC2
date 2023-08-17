"""Module for the DistributeInMeasurementVolume class."""

import attr
import mathutils    #type: ignore  # this is made available by the bpy module

from ....recipe.process_conditions.variabilities import UniformlyRandomLocationInMeasurementVolume
from ....recipe.blueprints import Particle
from ..state import RuntimeState
from .base import FeatureGenerationStep
from .set_based_mixin import SetBasedMixin


@attr.s(auto_attribs=True)
class DistributeInMeasurementVolume(SetBasedMixin, FeatureGenerationStep):
    """SynthChainStep to distribute particles in the measurement volume."""

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        location_variability = UniformlyRandomLocationInMeasurementVolume()

        for object_ in self.affected_set():
            if not isinstance(object_, Particle):
                raise ValueError("Set includes non-Particle objects (e.g."
                                 " MeasurementTechnique or Blueprint.)")

            blender_object = object_.blender_object

            if blender_object.parent is not None:
                continue

            new_location = mathutils.Vector(location_variability())
            blender_object.location = new_location

            # TODO: Check, if particle or one of it's children is outside the
            # measurement volume. If so, then roll new random positions, until the
            # particle and all of it's children are inside the measurement volume.
            # Only try this for a limited number of times, in case the agglomerate is so
            # large that it doesn't fit in the measurement volume. Additionally, at the
            # very beginning, we can check, if the bounding box of the agglomerate is
            # larger than the bounding box of the measurement volume in one of the three
            # dimensions. If this is the case, then we don't even need to try to
            # reposition the agglomerate.

        return runtime_state
