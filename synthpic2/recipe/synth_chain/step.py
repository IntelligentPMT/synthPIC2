"""Module for the SynthChainStep base class."""

from abc import ABC
from abc import abstractmethod

import attr

from .state import RuntimeState


@attr.s(auto_attribs=True)
class SynthChainStep(ABC):

    def __attrs_post_init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        """NotImplemented"""
