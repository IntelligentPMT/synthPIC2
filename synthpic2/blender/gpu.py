"""Blender GPU class."""

import warnings

import bpy

__all__ = ["Gpu"]


class Gpu:
    """Class to control Blenders access to GPU(s).

    Use this class to enable gpu for rendering. It throws a warning if
    gpu is not available.

    Example:
        >>> Gpu.enable()
    """

    @staticmethod
    def _make_available() -> None:
        """Enable GPUs in the main settings of Blender, if available."""
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons["cycles"].preferences

        # Enable all CPU and GPU devices
        cycles_preferences.get_devices()
        for device in cycles_preferences.devices:
            device.use = device.id != "CPU"

        # Attempt to set GPU device types if available
        for compute_device_type in ("CUDA", "OPENCL", "NONE"):
            try:
                cycles_preferences.compute_device_type = compute_device_type
                break
            except TypeError:
                pass

    @classmethod
    def enable(cls) -> None:
        """Enable GPU for Cycles, if there is at least one available."""

        cls._make_available()

        if cls._is_gpu_available():
            bpy.context.scene.cycles.device = "GPU"
        else:
            warnings.warn("GPU is not available.")

    @staticmethod
    def disable() -> None:
        """Disable GPU."""
        bpy.context.scene.cycles.device = "CPU"

    @staticmethod
    def _is_gpu_available() -> bool:
        """Check, if a GPU is available.

        Returns:
            is_gpu_available: True, if a GPU is available.
        """
        return bpy.context.preferences.addons["cycles"].preferences.has_active_device()
