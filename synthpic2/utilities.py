"""Module for synthpic2 utilities."""

import hashlib
import json
import pathlib
import random
from hydra.core import hydra_config
from typing import Any, List, Tuple

import numpy as np


def seed_everything(seed: int = 42) -> None:
    """Set seeds of `numpy.random` and `python.random`.

    Args:
        seed (int, optional): Random seed. Defaults to 42.
    """
    np.random.seed(seed)
    random.seed(seed)


def get_object_md5(obj: Any) -> str:
    return hashlib.md5(
        json.dumps(obj, default=lambda o: getattr(o, "__dict__", None),
                   sort_keys=True).encode()).hexdigest()


def get_unique_reproducible_random_colors(num_colors: int,
                                          alpha: float = 1
                                         ) -> List[Tuple[float, float, float, float]]:
    rng = np.random.RandomState(0)
    colors = rng.choice(range(1, 256**3), size=num_colors)

    r_list = ((colors >> 16) & 255) / 255
    g_list = ((colors >> 8) & 255) / 255
    b_list = (colors & 255) / 255

    a_list = np.ones_like(r_list) * alpha

    colors = np.stack([r_list, g_list, b_list, a_list])

    # A little cumbersome, but it makes mypy happy.
    return [(row[0], row[1], row[2], row[3]) for row in colors.T]


def get_hydra_output_root() -> pathlib.Path:
    """Get the output root path from Hydra.

    Returns:
        pathlib.Path: Output root path.
    """
    return pathlib.Path(hydra_config.HydraConfig.get().run.dir)
