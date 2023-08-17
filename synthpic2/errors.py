"""Custom exceptions."""

from .custom_types import AnyPath


class SynthPic2Error(Exception):
    """Base class for other exceptions."""
    pass


class ConventionError(SynthPic2Error):
    """Thrown, when a SynthPic2 convention is violated."""
    pass


class PrototypeNotFoundError(SynthPic2Error):
    """Exception to raise when a prototype cannot be found in a blend file."""

    def __init__(self, blend_file_path: AnyPath, name_in_blend_file: str) -> None:
        self.blend_file_path = blend_file_path
        self.name_in_blend_file = name_in_blend_file
        self.message = f"Couldn't find prototype '{name_in_blend_file}' in blend file \
            '{blend_file_path}'."

        super().__init__(self.message)


class PrototypeAlreadyExistsError(SynthPic2Error):
    """Thrown, when a prototype already exists."""

    def __init__(self, prototype_name: str) -> None:
        self.prototype_name = prototype_name
        self.message = f"Prototype '{self.prototype_name}' already exists."

        super().__init__(self.message)


class BlenderError(SynthPic2Error):
    """Raised, when an action caused a Blender error."""
    pass


class BlenderConventionError(SynthPic2Error):
    """Raised, when an action violates a Blender convention."""
    pass
