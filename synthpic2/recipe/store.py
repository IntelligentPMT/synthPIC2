"""Hydra config store, to allow accessing structured configs."""
from hydra.core.config_store import ConfigStore

from .recipe import Recipe


def populate() -> None:
    """Register configs."""
    recipe_store = ConfigStore.instance()
    recipe_store.store(name="BaseRecipe", node=Recipe, provider="synthpic2")
