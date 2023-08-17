"""Module for the MeasurementTechniqueRegistry class, which includes additional,
    measurement technique specific validation."""

from typing import Any

from ...errors import ConventionError
from .registry import Registry


class MeasurementTechniqueRegistry(Registry):
    """MeasurementTechniqueRegistry class, which includes additional,
        measurement technique specific validation."""

    def validate(self, item: Any) -> None:
        super().validate(item)

        if len(self.items) >= 1:
            raise ConventionError(
                "There may only be a single MeasurementTechnique per recipe.")
