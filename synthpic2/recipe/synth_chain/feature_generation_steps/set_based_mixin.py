"""Module for the SetBasedMixin."""

import attr

from ...registries import SET_REGISTRY


@attr.s(auto_attribs=True)
class SetBasedMixin:
    """Mixin for synth chain steps that operate on sets."""
    affected_set_name: str

    def __attrs_post_init__(self) -> None:
        self.affected_set = SET_REGISTRY.query(self.affected_set_name, strict=True)
