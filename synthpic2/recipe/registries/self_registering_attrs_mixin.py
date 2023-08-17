"""Module for the SelfRegisteringAttrsMixin class."""
from abc import ABC
from abc import abstractmethod

from .registry import Registry


class SelfRegisteringAttrsMixin(ABC):
    """Mixin for attrs classes, so that they register themselves in a predefined
    registry, after they have been initialized."""

    @property
    @abstractmethod
    def _registry(self) -> Registry:
        pass

    def __attrs_post_init__(self) -> None:
        self._registry.register(self)
