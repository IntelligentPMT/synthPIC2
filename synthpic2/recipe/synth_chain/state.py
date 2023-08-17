"""Module for the State class."""

from pathlib import Path
import tempfile
from typing import Optional
import uuid

import attr
import bpy
from omegaconf import MISSING
import yaml

from ...custom_types import AnyPath
from ..registries import Registry
from ..registries import SelfRegisteringAttrsMixin
from ..registries import STATE_REGISTRY


@attr.s(auto_attribs=True)
class RuntimeState:
    """Class to store and control the state of the runtime."""
    _target_: str = "synthpic2.recipe.synth_chain.state.RuntimeState"
    time: float = 0.0
    seed: int = MISSING


@attr.s(auto_attribs=True)
class State(SelfRegisteringAttrsMixin):
    """Class to handle blender states."""
    runtime_state: RuntimeState
    name: Optional[str] = None
    file_root: Optional[AnyPath] = None

    @property
    def _registry(self) -> Registry:
        return STATE_REGISTRY

    def __attrs_post_init__(self) -> None:
        if self.name is None:
            self.name = str(uuid.uuid4())

        super().__attrs_post_init__()

        if self.file_root is None:
            self.file_root = tempfile.mkdtemp()

        self.file_root = Path(self.file_root)
        self.file_root.mkdir(exist_ok=True, parents=True)

        self._blend_file_name = f"{self.name}.blend"
        self._blend_file_path = (self.file_root / self._blend_file_name).absolute()
        self._runtime_state_file_name = f"{self.name}.yaml"
        self._runtime_state_file_path = (self.file_root /
                                         self._runtime_state_file_name).absolute()

    def save_to_disk(self) -> None:
        with open(self._runtime_state_file_path, "w", encoding="utf-8") as yaml_file:
            yaml.dump(self.runtime_state, yaml_file)
        bpy.ops.wm.save_as_mainfile(filepath=str(self._blend_file_path))

        # Remove backup file that is automatically created by Blender, when a file is
        # overwritten.
        backup_file_path = Path(f"{self._blend_file_path}1")
        backup_file_path.unlink(missing_ok=True)

    def load_from_disk(self) -> None:
        with open(self._runtime_state_file_path, "r", encoding="utf-8") as yaml_file:
            self.runtime_state = yaml.load(yaml_file, Loader=yaml.Loader)
        bpy.ops.wm.open_mainfile(filepath=str(self._blend_file_path))

    def delete(self) -> None:
        self._blend_file_path.unlink(missing_ok=True)
        self._runtime_state_file_path.unlink(missing_ok=True)

        self.unregister()

    def unregister(self) -> None:
        assert isinstance(self.name, str)
        self._registry.delete_item(self.name)
