"""Custom type definitions."""
import os
from typing import Dict, Union, TypeAlias

import bpy

AnyPath = Union[str, os.PathLike[str]]

RenamingMap = Dict[str, str]
BlenderDataBlock: TypeAlias = Union[bpy.types.Object, bpy.types.Mesh,
                                    bpy.types.Material, bpy.types.Texture,
                                    bpy.types.ParticleSettings,
                                    bpy.types.GeometryNodeTree]
