""" Module for the prototype library."""

from pathlib import Path
from typing import Type

import hydra
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from .errors import ConventionError
from .recipe.prototypes.prototypes import _Prototype
from .recipe.prototypes.prototypes import GeometryPrototype
from .recipe.prototypes.prototypes import MaterialPrototype
from .recipe.prototypes.prototypes import MeasurementTechniquePrototype


class PrototypeLibrary:
    """A library to load prototypes."""

    root = Path(__file__).parent.parent / "prototype_library"

    @classmethod
    def load(cls) -> None:
        cls.load_prototypes("geometries", GeometryPrototype)
        cls.load_prototypes("materials", MaterialPrototype)
        cls.load_prototypes("measurement_techniques", MeasurementTechniquePrototype)

    @classmethod
    def load_prototypes(cls, subfolder_name: str,
                        prototype_type: Type[_Prototype]) -> None:

        folder_path = cls.root / subfolder_name

        if not folder_path.exists():
            raise FileNotFoundError(f"Library folder {subfolder_name} does not exist.")

        blend_file_paths = list(folder_path.glob("*.blend"))

        for blend_file_path in blend_file_paths:
            prototype_name = blend_file_path.stem
            yaml_file_path = blend_file_path.parent / (blend_file_path.stem + ".yaml")

            if not blend_file_path.exists():
                raise FileNotFoundError(
                    f"{yaml_file_path} has no accompanying blend file "
                    f"{blend_file_path}.")

            config = OmegaConf.structured(prototype_type)

            config.name = prototype_name
            config.blend_file_path = str(blend_file_path)

            if yaml_file_path.exists():
                GlobalHydra.instance().clear()
                with hydra.initialize_config_dir(
                        config_dir=str(folder_path.absolute())):
                    config_addendum = hydra.compose(config_name=prototype_name)
                    if "name" in config_addendum:
                        raise ConventionError(
                            "Prototype library YAMLs should not specify a `name`, "
                            "since it is being assigned automatically.")
                    if "blend_file_path" in config_addendum:
                        raise ConventionError(
                            "Prototype library YAMLs should not specify a "
                            "`blend_file_path`, since it is being assigned "
                            "automatically.")

                # If the prototype overrides the target class, then a structured config
                # might complain about missing/new fields. Therefore, we need to disable
                # the `struct` flag.
                if "_target_" in config_addendum:
                    OmegaConf.set_struct(config, False)

                config = OmegaConf.merge(config, config_addendum)

            hydra.utils.instantiate(config, _convert_="all")
