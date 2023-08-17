"""Useful Blender functions that don't have their final place yet."""
import pathlib
import re
from typing import Dict, Optional, Tuple

import bmesh    # type: ignore
import bpy
from matplotlib.colors import rgb2hex
import numpy as np
from pyvirtualdisplay.display import Display
import trimesh
from contextlib import contextmanager

from ..custom_types import AnyPath
from ..custom_types import BlenderDataBlock
from ..custom_types import RenamingMap
from ..errors import BlenderConventionError
from ..errors import ConventionError


def duplicate_and_assign_material(object_: bpy.types.Object, material_name: str,
                                  suffix: str) -> Dict[str, RenamingMap]:
    """Copy a material with given `material_name` and assign it to a given `_object`.

    Args:
        object_ (bpy.types.Object): Blender object to assign the material to.
        material_name (str): the name of the material
        suffix (str): suffix that is appended to the name of the material
    """
    material = get_material(material_name)
    material = material.copy()
    material.name = material_name + suffix

    assign_material(object_, material.name)

    return {"Material": {material_name: material.name}}


def assign_material(object_: bpy.types.Object, material_name: str) -> None:
    """Assign a material with given `material_name` and to a given `_object`.

    Args:
        object_ (bpy.types.Object): Blender object to assign the material to.
        material_name (str): the name of the material
    """
    material = get_material(material_name)

    object_materials = object_.data.materials
    object_materials.clear()
    object_materials.append(material)


def adapt_interface_iors(
    material_name_outside: str,
    material_name_inside: str,
) -> None:
    """Calculate the effective index of refraction (IOR) for a refractive material
    inside another refractive material, based on the vacuum IORs of both materials.

    In Blender: The outside object "sees" blue normals, while the inside object "sees"
    red normals.

    Args:
        material_name_outside (str): Name of the Blender material that is on the
            outside.
        material_name_inside (str): Name of the Blender material that is on the inside.

    Raises:
        ConventionError: Raised, if the outside material has multiple nodes with IORs.
    """

    material_inside = get_material(material_name_inside)
    material_outside = get_material(material_name_outside)

    nodes_with_ior_in_outside_material = [
        node for node in material_outside.node_tree.nodes if "IOR" in node.inputs
    ]

    if len(nodes_with_ior_in_outside_material) != 1:
        raise ConventionError(
            "Outside material must have exactly one node with an IOR value.")

    object_outside_ior_vacuum_value = nodes_with_ior_in_outside_material[0].inputs[
        "IOR"].default_value

    for node in material_inside.node_tree.nodes:
        if "IOR" in node.inputs:
            object_inside_ior_vacuum_value = node.inputs["IOR"].default_value
            interface_ior_from_outside_to_inside = \
                object_inside_ior_vacuum_value / object_outside_ior_vacuum_value
            node.inputs["IOR"].default_value = interface_ior_from_outside_to_inside


def render_to_file(output_path: AnyPath) -> None:
    """Renders an image to a file. The output root will be created, if necessary.

    Args:
        output_path (AnyPath): Path of the output image file.
    """

    output_path = pathlib.Path(output_path).resolve()

    output_root = output_path.parent
    output_root.mkdir(exist_ok=True)

    file_name = output_path.stem

    file_format = output_path.suffix.upper().lstrip(".")    # without dot

    if file_format:
        try:
            bpy.context.scene.render.image_settings.file_format = file_format
        except TypeError as error:
            if len(error.args) == 1:
                match = re.search(r"not found in \((.*)\)", error.args[0])
                if match is None:
                    raise error
                else:
                    raise ValueError(
                        f"Blender does not support the specified file format "
                        f"({file_format}). Valid file formats are: {match.group(1)}."
                    ) from error
            else:
                raise error

    bpy.context.scene.render.filepath = str(output_root / file_name)

    with Display():
        bpy.ops.render.render(write_still=True)


class _RenamingTracker:
    """Helper class to copy data blocks of blender objects and keep track of their
    renaming."""

    renaming_maps: Dict[str, RenamingMap] = {}

    def __init__(self, suffix: str):
        self.suffix = suffix

    def copy(self, data_block: BlenderDataBlock) -> BlenderDataBlock:
        original_name = data_block.name
        data_block = data_block.copy()
        data_block.name = original_name + self.suffix
        data_type = data_block.bl_rna.name

        if "Texture" in data_type:
            data_type = "Texture"

        self.renaming_maps[data_type] = {original_name: data_block.name}
        return data_block


def duplicate_and_link_object(
    object_: bpy.types.Object, duplicate_name_suffix: str,
    target_collection: bpy.types.Collection
) -> Tuple[bpy.types.Object, Dict[str, RenamingMap]]:
    """Creates an independent duplicate of a blender object and links it to a
        collection.

    Args:
        object_ (bpy.types.Object): object to be duplicated
        duplicate_name_suffix (str): suffix for the name of the duplicate
        target_collection (bpy.types.Collection): collection, to which the object will
            be linked

    Returns:
        bpy.types.Object: duplicate
        Dict[str, RenamingMap]: RenamingMap with information on how relevant data blocks
            were renamed.
    """
    # TODO: Check if anything else needs to be copied (maybe improve unittest).
    renaming_tracker = _RenamingTracker(suffix=duplicate_name_suffix)

    original_transform = object_.matrix_world.copy()

    duplicate = renaming_tracker.copy(object_)

    # Un-parent the object so that we don't have any relationship between the duplicate
    # and the parent of the original. This also requires restoring it's position in the
    # world.
    duplicate.parent = None
    duplicate.matrix_world = original_transform

    target_collection.objects.link(duplicate)

    duplicate.data = renaming_tracker.copy(object_.data)

    for material_slot in duplicate.material_slots:
        material_slot.material = renaming_tracker.copy(material_slot.material)

    for particle_system in duplicate.particle_systems:
        particle_system.settings = renaming_tracker.copy(particle_system.settings)

    for modifier in duplicate.modifiers:
        if hasattr(modifier, "node_group"):
            modifier.node_group = renaming_tracker.copy(modifier.node_group)

        if hasattr(modifier, "texture"):
            if modifier.texture is not None:
                modifier.texture = renaming_tracker.copy(modifier.texture)

    return duplicate, renaming_tracker.renaming_maps


def replace_object_material(object_: bpy.types.Object, old_material_name: str,
                            new_material_name: str) -> None:
    """Replace the material of an object (specified by its name) with a new material
        (specified by its name).

    Source:
        https://blender.stackexchange.com/questions/53366/how-can-i-replace-a-material-from-python

    Raises:
        ValueError: Raised, if the object does not use a material named
            `old_material_name`.

    Args:
        object_ (bpy.types.Object): blender object, whose material shall be replaced
        old_material_name (str): name of the old material
        new_material_name (str): name of the new material
    """

    new_material = get_material(new_material_name)

    current_material_names = [slot.material.name for slot in object_.material_slots]

    # TODO: Copy data (materials, nodes, meshes, textures) explicitly.

    if old_material_name not in current_material_names:
        raise ValueError(f"Object does not use material: {old_material_name}")

    # Iterate over the material slots and replace the specified material.
    for slot in object_.material_slots:
        if slot.material.name == old_material_name:
            slot.material = new_material


def get_material(material_name: str) -> bpy.types.Material:
    """Returns a blender material with the specified name.

    Args:
        material_name (str): Name of the material to return.

    Raises:
        ValueError: Raised, if the material does not exist.

    Returns:
        bpy.types.Material: Blender material
    """

    materials = bpy.data.materials

    if material_name not in materials:
        raise ValueError(f"No material with name: {material_name}")

    return materials[material_name]


def add_object_to_collection(object_: bpy.types.Object, collection_name: str) -> None:
    bpy.data.collections[collection_name].objects.link(object_)


def get_object(object_name: str) -> bpy.types.Object:
    """Returns a blender object with the specified name.

    Args:
        object_name (str): Name of the object to return.

    Raises:
        ValueError: Raised, if the object does not exist.

    Returns:
        bpy.types.Object: Blender object
    """

    objects = bpy.data.objects

    if object_name not in objects:
        raise ValueError(f"No object with name: {object_name}")

    return objects[object_name]


def get_collection(collection_name: str) -> bpy.types.Collection:
    """Returns a blender collection with the specified name.

    Args:
        collection_name (str): Name of the collection to return.

    Raises:
        ValueError: Raised, if the collection does not exist.

    Returns:
        bpy.types.Collection: Blender collection
    """

    collections = bpy.data.collections

    if collection_name not in collections:
        raise ValueError(f"No collection with name: {collection_name}")

    return collections[collection_name]


def create_collection(collection_name: str,
                      scene: Optional[bpy.types.Scene] = None) -> bpy.types.Collection:
    """Create a collection with name `collection_name` and link it to the given scene.

    Args:
        collection_name (str): name of the new collection.
        scene (Optional[bpy.types.Scene], optional): Scene that the collection is
            linked to. Defaults to None, which means that the collection is linked to
            the scene in context.

    Returns:
        bpy.types.Collection: the new collection
    """

    if collection_name in bpy.data.collections:
        #? Alternatively, we could just return the existing collection.
        raise ValueError(f"Collection already exists: {collection_name}")

    if scene is None:
        scene = bpy.context.scene

    collection = bpy.data.collections.new(collection_name)
    assert scene is not None
    scene.collection.children.link(collection)

    return collection


def flip_face_normals_with_material_name(object_: bpy.types.Object,
                                         material_name: str) -> None:
    """Flip normals of the object faces, if the faces use a certain material.

    Args:
        object_ (bpy.types.Object): [description]
        material_name (str): Name of the material to identify faces to flip.
    """
    if len(object_.material_slots) == 0:    # ? Should we raise an error here?
        return

    for face in object_.data.polygons:
        if object_.material_slots[face.material_index] == material_name:
            face.flip()


def replace_material(object_: bpy.types.Object, old_material_name: str,
                     new_material_name: str) -> None:
    """Replace the material of an object with a new material (both identified by their
        names).

    Args:
        object (bpy.types.Object): object for which we are replacing the material
        old_material (str): the old material name
        new_material (str): the new material name
    """
    new_material = get_material(new_material_name)
    # Iterate over the material slots and replace the material
    for material_slot in object_.material_slots:
        if material_slot.material.name == old_material_name:
            material_slot.material = new_material


def create_emission_shader(color: Tuple[float, float, float,
                                        float,] = (1, 1, 1, 1)) -> bpy.types.Material:
    """Create an emission shader with a specified color and a strength of 1.

    Taken from https://vividfax.github.io/2021/01/14/blender-materials.html

    Args:
        color (Tuple[float,float,float,float,], optional): 4-Tuple (RGBA) of floats
            between 0 and 1. Defaults to (1,1,1,1).

    Returns:
        bpy.types.Material
    """

    material_name = "Emission" + rgb2hex(color)    # type: ignore
    material = bpy.data.materials.get(material_name)

    if material is None:
        material = bpy.data.materials.new(name=material_name)

    material.use_nodes = True
    if material.node_tree:
        material.node_tree.links.clear()
        material.node_tree.nodes.clear()

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new(type="ShaderNodeOutputMaterial")

    emission_node = nodes.new(type="ShaderNodeEmission")
    emission_node.inputs["Color"].default_value = color
    emission_node.inputs["Strength"].default_value = 1

    links.new(emission_node.outputs["Emission"], output.inputs["Surface"])
    material.use_fake_user = True

    return material


def set_rigidity(object_: bpy.types.Object, state: bool) -> None:
    """Set the rigidity of a given object.

    Args:
        state (bool): new rigidity state
    """

    with selected_only(object_):
        if state:
            bpy.ops.rigidbody.object_add()
        else:
            bpy.ops.rigidbody.object_remove()


@contextmanager
def selected_only(object_: bpy.types.Object):
    """Temporarily select the given `object_`.

    Args:
        object_ (bpy.types.Object): Object to be temporarily selected.

    Yields:
        bpy.types.Object: The selected object.
    """

    # TODO: Allow multiple objects to be selected.

    previous_selection = [o for o in bpy.context.scene.objects if o.select_get()]

    is_visible = object_.hide_viewport
    object_.hide_viewport = False
    select_only(object_)
    object_.hide_viewport = is_visible
    try:
        yield object_
    finally:
        for obj in previous_selection:
            obj.select_set(True)


def select_only(object_: bpy.types.Object) -> None:
    """Deselect all objects, select and activate the given `object_`.

    Args:
        object_ (bpy.types.Object): object to be selected and activated.
    """
    deselect_all()
    activate(object_)
    select(object_)


def delete(object_: bpy.types.Object) -> None:
    """Delete the `object_`.

    Args:
        object_ (bpy.types.Object): object to be deleted.
    """
    bpy.data.objects.remove(object_, do_unlink=True)


def convert_blender_object_to_blender_mesh(
        object_: bpy.types.Object) -> bpy.types.Object:
    """Convert a blender object to a blender mesh and restore the transformation and
    parent/child relation of potential children.

    Args:
        object_ (bpy.types.Object): object to be converted.

    Returns:
        bpy.types.Object: converted mesh object.
    """
    select_only(object_)
    original_name = object_.name

    # When we convert an object with children, the children are un-parented, without
    # keeping track of their transforms. So we have to keep track ourselves.
    original_transformations = {
        child: child.matrix_world.copy() for child in object_.children
    }

    bpy.ops.object.convert(target="MESH")
    object_ = bpy.context.object
    object_.name = original_name

    for child, original_transform in original_transformations.items():
        # Restore the transforms and parent/child relations.
        child.matrix_world = original_transform
        set_parent(child, object_, keep_transform=True)
    return object_


def convert_blender_object_to_trimesh(object_: bpy.types.Object) -> trimesh.Trimesh:
    object_copy, _ = duplicate_and_link_object(
        object_,
        duplicate_name_suffix="_copy",
        target_collection=bpy.data.collections[0])

    select_only(object_copy)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    object_copy = convert_blender_object_to_blender_mesh(object_copy)

    bm = bmesh.new()
    bm.from_mesh(object_copy.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    vertices = np.asarray([vertex.co for vertex in bm.verts])
    faces = np.asarray([[vertex.index for vertex in face.verts] for face in bm.faces])
    bm.free()

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    delete(object_copy)
    return mesh


def set_parent(child: bpy.types.Object,
               parent: bpy.types.Object | None,
               keep_transform: bool = False) -> None:
    child.parent = parent
    update_dependency_graph()

    if parent is None:
        return

    if keep_transform:
        child.matrix_parent_inverse = parent.matrix_world.inverted()


def update_dependency_graph() -> None:
    blender_dependency_graph = bpy.context.evaluated_depsgraph_get()
    blender_dependency_graph.update()


def hide_in_render(object_: bpy.types.Object) -> None:
    object_.hide_render = True


def show_in_render(object_: bpy.types.Object) -> None:
    object_.hide_render = False


def select(object_: bpy.types.Object) -> None:
    if object_.hide_viewport:
        raise BlenderConventionError(
            f"Object must be visible to be selected. However, {object_.name} is hidden."
        )
    object_.select_set(True)


def deselect(object_: bpy.types.Object) -> None:
    object_.select_set(False)


def deselect_all() -> None:
    for object_ in bpy.data.objects:
        object_.select_set(False)


def activate(object_: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = object_


set_context = activate


def export_selected_objects_as_stl(output_path: AnyPath) -> None:
    """Exports selected objects of the current blender scene as stl file. The output
        root will be created, if necessary.

    Args:
        output_path (AnyPath): Path of the output image file.
    """

    output_path = pathlib.Path(output_path).resolve()

    output_root = output_path.parent
    output_root.mkdir(exist_ok=True)

    bpy.ops.export_mesh.stl(filepath=str(output_path),
                            check_existing=False,
                            use_selection=True)
