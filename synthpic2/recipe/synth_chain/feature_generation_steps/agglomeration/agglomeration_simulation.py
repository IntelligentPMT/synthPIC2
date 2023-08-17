"""Module for cluster-cluster and particle-cluster agglomeration."""

import random

from .agglomerate import Agglomerate
from .collision_matrix import CollisionMatrix


def agglomeration(
        primary_particles: list[Agglomerate],
        mode: str,    # can be "cluster-cluster" or "particle-cluster"
        randomness: float,
        translation_speed: float,
        sintering_ratio: float = 0,
        rotation_speed: float = 0) -> Agglomerate:
    """Simulate agglomeration of particles.

    Args:
        primary_particles (list[Agglomerate]): List of primary particles (agglomerates
            without children).
        mode (str): Agglomeration mode
            "cluster-cluster" or
            "particle-cluster"
        translation_speed (float): Relative translation step size, between two
            collision checks.
        randomness (float): Number between 0 and 1, to control the randomness of the
            random walk:
                0 = straight translation, constant rotation
                1 = completely random walk, stochastic rotation
        sintering_ratio (float, optional): Number between 0 and 1, to control how
            close the centers of mass of the two touching primary particles will be
            after the collision:
                0 = particles will just barely touch after the collision
                1 = centers of mass will be identical
            Defaults to 0.
        rotation_speed (float, optional): Sum of the rotation intervals in x-, y-
            and z-direction between two collision checks, for both collision
            partners, as fraction of 360 degrees.
            Defaults to 0.

    Raises:
        ValueError: if an unknown agglomeration mode is specified

    Returns:
        Agglomerate: agglomerated primary particles
    """

    if len(primary_particles) == 1:
        return primary_particles[0]

    if mode.lower() == "cluster-cluster":
        agglomerate = cluster_cluster_agglomeration(primary_particles,
                                                    translation_speed=translation_speed,
                                                    randomness=randomness,
                                                    sintering_ratio=sintering_ratio,
                                                    rotation_speed=rotation_speed)
    elif mode.lower() == "particle-cluster":
        agglomerate = particle_cluster_agglomeration(
            primary_particles,
            translation_speed=translation_speed,
            randomness=randomness,
            sintering_ratio=sintering_ratio,
            rotation_speed=rotation_speed)
    else:
        raise ValueError(f"Unknown agglomeration mode: {mode}")

    return agglomerate


def particle_cluster_agglomeration(primary_particles: list[Agglomerate],
                                   translation_speed: float,
                                   randomness: float,
                                   sintering_ratio: float = 0,
                                   rotation_speed: float = 0) -> Agglomerate:
    """Simulate particle-cluster agglomeration of particles (i.e. one by one).

    Args:
        primary_particles (list[Agglomerate]): List of primary particles (agglomerates
            without children).
        translation_speed (float): Relative translation step size, between two
            collision checks.
        randomness (float): Number between 0 and 1, to control the randomness of the
            random walk:
                0 = straight translation, constant rotation
                1 = completely random walk, stochastic rotation
        sintering_ratio (float, optional): Number between 0 and 1, to control how
            close the centers of mass of the two touching primary particles will be
            after the collision:
                0 = particles will just barely touch after the collision
                1 = centers of mass will be identical
            Defaults to 0.
        rotation_speed (float, optional): Sum of the rotation intervals in x-, y-
            and z-direction between two collision checks, for both collision
            partners, as fraction of 360 degrees.
            Defaults to 0.

    Returns:
        Agglomerate: agglomerated primary particles
    """

    shuffled_agglomerates = random.sample(primary_particles, len(primary_particles))
    mother_agglomerate = shuffled_agglomerates[0]

    for agglomerate in shuffled_agglomerates[1:]:
        mother_agglomerate.collide(agglomerate,
                                   translation_speed=translation_speed,
                                   randomness=randomness,
                                   sintering_ratio=sintering_ratio,
                                   rotation_speed=rotation_speed)

    return mother_agglomerate


def cluster_cluster_agglomeration(primary_particles: list[Agglomerate],
                                  translation_speed: float,
                                  randomness: float,
                                  sintering_ratio: float = 0,
                                  rotation_speed: float = 0) -> Agglomerate:
    """Simulate cluster-cluster agglomeration of particles (i.e. in form of a binary
        tree).

    Args:
        primary_particles (list[Agglomerate]): List of primary particles (agglomerates
            without children).
        translation_speed (float): Relative translation step size, between two
            collision checks.
        randomness (float): Number between 0 and 1, to control the randomness of the
            random walk:
                0 = straight translation, constant rotation
                1 = completely random walk, stochastic rotation
        sintering_ratio (float, optional): Number between 0 and 1, to control how
            close the centers of mass of the two touching primary particles will be
            after the collision:
                0 = particles will just barely touch after the collision
                1 = centers of mass will be identical
            Defaults to 0.
        rotation_speed (float, optional): Sum of the rotation intervals in x-, y-
            and z-direction between two collision checks, for both collision
            partners, as fraction of 360 degrees.
            Defaults to 0.

    Returns:
        Agglomerate: agglomerated primary particles
    """

    shuffled_agglomerates = random.sample(primary_particles, len(primary_particles))
    collision_matrix = CollisionMatrix(shuffled_agglomerates)

    while collision_matrix.num_collision_partners > 1:
        collision_pair = collision_matrix.pick_collision_pair()
        collision_pair[0].collide(agglomerate_other=collision_pair[1],
                                  translation_speed=translation_speed,
                                  randomness=randomness,
                                  sintering_ratio=sintering_ratio,
                                  rotation_speed=rotation_speed)
        collision_matrix.update_collision_partner(
            collision_partner_update=collision_pair[0])

        collision_matrix.remove_collision_partner(collision_partner=collision_pair[1])

    final_agglomerate = collision_matrix.collision_partners[0]

    return final_agglomerate
