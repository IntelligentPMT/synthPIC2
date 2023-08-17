"""Module for the class CollisionMatrix."""

import random

import numpy as np

from .agglomerate import Agglomerate


class CollisionMatrix:
    """Class to represent a collision matrix."""

    def __init__(self, agglomerates: list[Agglomerate]):
        self.collision_partners = agglomerates
        self.calculate_content()

    @property
    def normalized_content(self) -> np.ndarray:
        return self.content / np.amax(self.content)

    @property
    def num_collision_partners(self) -> int:
        return len(self.collision_partners)

    def calculate_content(self) -> None:
        """Calculate the content of the collision matrix."""

        collision_matrix = np.zeros(shape=(self.num_collision_partners,
                                           self.num_collision_partners))

        for i, collision_partner_a in enumerate(self.collision_partners):
            for j, collision_partner_b in enumerate(self.collision_partners):
                if i >= j:
                    continue

                collision_frequency = self._calculate_collision_frequency(
                    collision_partner_a, collision_partner_b)

                collision_matrix[i][j] = collision_frequency
                collision_matrix[j][i] = collision_frequency

        self.content = collision_matrix

    @staticmethod
    def _calculate_collision_frequency(collision_partner_a: Agglomerate,
                                       collision_partner_b: Agglomerate) -> float:
        return ((collision_partner_a.radius_gyration +
                 collision_partner_b.radius_gyration)**2 *
                np.sqrt(1 / collision_partner_a.mass + 1 / collision_partner_b.mass))

    def pick_collision_pair(self) -> tuple[Agglomerate, Agglomerate]:
        """Pick a pair for the next collision, based on an acceptance–rejection
            strategy.

        Source:
            Wei, Kruis (2013) - A GPU-based parallelized Monte-Carlo method for particle
                                coagulation using an acceptance–rejection strategy

        Returns:
            tuple[Agglomerate, Agglomerate]: A pair of agglomerates for the next
                collision.
        """
        collision_probability = 0.0
        random_threshold = 1.0
        collision_partner_i = -1
        collision_partner_j = -1

        while collision_probability <= random_threshold:
            collision_partner_i = np.random.randint(self.num_collision_partners)
            collision_partner_j = np.random.randint(self.num_collision_partners)

            random_threshold = random.uniform(0.0, 1.0)

            collision_probability = \
                self.normalized_content[collision_partner_i][collision_partner_j]

        collision_pair = (self.collision_partners[collision_partner_i],
                          self.collision_partners[collision_partner_j])

        return collision_pair

    def update_collision_partner(self, collision_partner_update: Agglomerate) -> None:
        """Update the collision frequency of a collision partner, after it has changed
            due to a collision.

        Args:
            collision_partner_update (Agglomerate): Collision partner to update.
        """
        idx_collision_partner_update = self.collision_partners.index(
            collision_partner_update)

        for i, collision_partner_a in enumerate(self.collision_partners):
            for j, collision_partner_b in enumerate(self.collision_partners):
                if idx_collision_partner_update in (i, j):
                    if i >= j:
                        continue
                    collision_frequency = self._calculate_collision_frequency(
                        collision_partner_a, collision_partner_b)
                    self.content[i][j] = collision_frequency
                    self.content[j][i] = collision_frequency

    def remove_collision_partner(self, collision_partner: Agglomerate) -> None:
        """Remove a collision partner from the matrix, after it has been used for a
            collision.

        Args:
            collision_partner (Agglomerate): Collision partner to be removed.
        """
        collision_partner_index = self.collision_partners.index(collision_partner)

        self.collision_partners.pop(collision_partner_index)

        self.content = np.delete(self.content, obj=collision_partner_index, axis=0)
        self.content = np.delete(self.content, obj=collision_partner_index, axis=1)
