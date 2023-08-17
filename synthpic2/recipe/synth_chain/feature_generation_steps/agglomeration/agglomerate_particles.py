"""Module for AgglomerateParticles synth chain step."""

from typing import Any
import attr
import numpy as np

from ....blueprints import Particle
from ...state import RuntimeState
from ..base import FeatureGenerationStep
from ..set_based_mixin import SetBasedMixin
from .agglomerate import Agglomerate
from .agglomeration_simulation import agglomeration


@attr.s(auto_attribs=True)
class AgglomerateParticles(SetBasedMixin, FeatureGenerationStep):
    """FeatureGenerationStep to simulate gas phase agglomeration."""
    mode: str    # can be "cluster-cluster" or "particle-cluster"
    randomness: float
    speed: float
    sintering_ratio: float = 0
    primary_particle_number_variability: Any = None

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:

        affected_particles: list[Particle] = self.affected_set()
        subsets: list[list[Particle]] = []

        if self.primary_particle_number_variability is None:
            subsets = [affected_particles]
        else:
            num_remaining_particles = len(affected_particles)
            while num_remaining_particles > 0:

                # Check if self.primary_particle_number_variability is a function
                if not callable(self.primary_particle_number_variability):
                    raise ValueError(
                        "primary_particle_number_variability must be a callable.")

                num_particles_in_subset = self.primary_particle_number_variability()    # pylint: disable=not-callable

                # Check if self.primary_particle_number_variability returns a single
                # positive number.
                if isinstance(num_particles_in_subset, np.ndarray):
                    num_particles_in_subset = num_particles_in_subset.squeeze()
                    if num_particles_in_subset.shape != ():
                        raise ValueError(
                            "primary_particle_number_variability must return only a"
                            " single number.")
                    else:
                        num_particles_in_subset = num_particles_in_subset.item()

                if not isinstance(num_particles_in_subset, (int, float)):
                    raise ValueError(
                        "primary_particle_number_variability must return only a single"
                        " number.")

                if num_particles_in_subset < 0:
                    raise ValueError(
                        "primary_particle_number_variability must return only positive"
                        " numbers.")

                # If there are not enough particles left to fill the subset, fill it
                # with the remaining particles.
                num_particles_in_subset = int(
                    min(np.ceil(num_particles_in_subset), num_remaining_particles))

                num_remaining_particles -= num_particles_in_subset

                # Take the first num_particles_in_subset particles from the list, store
                # them in a subset and remove them from the list of affected particles.
                subset = affected_particles[:num_particles_in_subset]
                affected_particles = affected_particles[num_particles_in_subset:]

                subsets.append(subset)

        for subset in subsets:
            if len(subset) <= 1:
                continue

            agglomerates = [
                Agglomerate.from_blender(particle.blender_object) for particle in subset
            ]

            final_agglomerate = agglomeration(agglomerates,
                                              mode=self.mode,
                                              translation_speed=self.speed,
                                              randomness=self.randomness,
                                              sintering_ratio=self.sintering_ratio)

            final_agglomerate.to_blender()

        return runtime_state
