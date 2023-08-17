"""Module for the RenderPreparationMixin class."""

from abc import ABC


class RenderPreparationMixin(ABC):
    """A mixin for classes to equip them with methods to prepare the rendering."""

    def prepare_for_render(self, rendering_mode: str)->None:
        match rendering_mode.lower():
            case "real":
                self._prepare_real_rendering_mode()
            case "categorical":
                self._prepare_categorical_rendering_mode()
            case "stylized":
                self._prepare_stylized_rendering_mode()
            case "stylized_xray":
                self._prepare_stylized_xray_rendering_mode()
            case "normal_map":
                self._prepare_normal_map_rendering_mode()
            case "depth_map":
                self._prepare_depth_map_rendering_mode()
            case "stl":
                self._prepare_stl_rendering_mode()
            case _:
                raise ValueError(f"Unsupported rendering mode: {rendering_mode}")

    def _prepare_real_rendering_mode(self)->None:
        pass

    def _prepare_categorical_rendering_mode(self)->None:
        pass

    def _prepare_stylized_rendering_mode(self)->None:
        pass

    def _prepare_stylized_xray_rendering_mode(self)->None:
        pass

    def _prepare_normal_map_rendering_mode(self)->None:
        pass

    def _prepare_depth_map_rendering_mode(self)->None:
        pass

    def _prepare_stl_rendering_mode(self)->None:
        pass
