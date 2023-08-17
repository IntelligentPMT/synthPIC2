"""Module for RelaxCollisions synth chain step."""

import attr
import trimesh
import bpy
import mathutils    # type: ignore  # this is made available by the bpy module
import uuid

import numpy as np
from typing import Optional, Tuple

from ....blender.utilities import select_only
from ....blender.utilities import set_parent
from ....blender.utilities import set_rigidity
from ....blender.utilities import convert_blender_object_to_trimesh
from ....blender.utilities import convert_blender_object_to_blender_mesh
from ....blender.utilities import set_context
from ..rendering_steps.state import SaveState
from ..state import RuntimeState
from .base import FeatureGenerationStep
from .set_based_mixin import SetBasedMixin
from synthpic2.recipe.synth_chain.state import State


def _convert_to_mesh_recursively(blender_object: bpy.types.Object) -> None:
    """Recursively iterate through a tree of blender objects, and starting from
    the leaves and working up to the root, convert the objects to meshes. Unfortunately,
    this breaks parent/child relations, so we have an option to restore them _and_ it
    also breaks the references to blender objects, so we set the context object to the
    ultimate parent.

    Args:
        blender_object (bpy.types.Object): Blender object (potentially with children) to
            convert to mesh.
    """
    if blender_object.children:
        for child in blender_object.children:
            _convert_to_mesh_recursively(child)

    if blender_object.type != "MESH":
        blender_object = convert_blender_object_to_blender_mesh(blender_object)

    set_context(blender_object)


@attr.s(auto_attribs=True)
class RelaxCollisions(SetBasedMixin, FeatureGenerationStep):
    """SynthChainStep to relax collisions between objects of a set, using Blenders
        bullet physics engine."""
    damping: Optional[float] = None
    angular_damping: Optional[float] = None
    linear_damping: Optional[float] = None
    friction: float = 1
    restitution: float = 1
    mass: float = 1.0
    collision_shape: str = "MESH"
    mesh_source: str = "FINAL"
    num_frames: int = 100
    use_gravity: bool = False
    gravity: Tuple[float, float, float] = (0, 0, -9.81)
    collision_margin: float = 1E-6
    time_scale: float = 1.0
    substeps_per_frame: int = 10
    solver_iterations: int = 10
    dry_run: bool = False

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:

        # Damping is a convenience parameter that sets both angular and linear damping
        # in Blender and has no effect on the simulation if only the damping parameter
        # is available.
        if self.damping is None:
            self.damping = 0.9999999
        else:
            if self.angular_damping is not None or self.linear_damping is not None:
                raise ValueError(
                    "Either damping or angular_damping/translation_damping can be"
                    " set, but not both.")

        if self.angular_damping is None:
            self.angular_damping = self.damping

        if self.linear_damping is None:
            self.linear_damping = self.damping

        # TODO: Catch potential blender errors for false string inputs already in Hydra,
        #   probably using Enums.

        # Save the original state to disk for later restoration
        original_state = State(runtime_state=runtime_state)
        original_state.save_to_disk()

        # we use the convention that there is only one scene
        scene = bpy.data.scenes[0]

        scene.use_gravity = self.use_gravity
        scene.gravity = self.gravity

        if scene.rigidbody_world is None:
            bpy.ops.rigidbody.world_add()

        assert scene.rigidbody_world is not None    # this is to make mypy happy
        scene.rigidbody_world.enabled = True
        scene.rigidbody_world.time_scale = self.time_scale
        scene.rigidbody_world.substeps_per_frame = self.substeps_per_frame
        scene.rigidbody_world.solver_iterations = self.solver_iterations

        # Save affected objects so that we don't have to compute the set multiple times.
        affected_particle_objects = [
            particle.blender_object for particle in self.affected_set()
        ]

        # Iterate all meta ball objects and rename them, so that they no longer interact
        # and save the renaming mapping by the original name and new name for later
        # restoration.
        renaming_mapping: dict[str, str] = {}
        for blender_object in affected_particle_objects:
            if blender_object.type == "META":
                old_name = blender_object.name
                new_name = uuid.uuid4().hex    # generate unique string
                blender_object.name = new_name
                renaming_mapping[new_name] = old_name

        # Ultimate parents are the objects that have not parents.
        ultimate_parents = [
            blender_object for blender_object in affected_particle_objects
            if blender_object.parent is None
        ]

        # Convert all particles that are no meshes to meshes. This is necessary because
        # objects like meta balls don't support rigid body physics.
        ultimate_parents_new: list[bpy.types.Object] = []
        for ultimate_parent in ultimate_parents:
            _convert_to_mesh_recursively(ultimate_parent)
            ultimate_parents_new.append(bpy.context.object)
        ultimate_parents = ultimate_parents_new

        # Iterate all ultimate parents and change the properties of the descendants
        # and the ultimate parents themselves. What we do here is to set the rigid body
        # properties and introduce a center of mass object for each agglomerate that
        # acts as compound parent for all sub-objects.
        center_of_mass_objects: list[bpy.types.Object] = []
        for ultimate_parent in ultimate_parents:
            descendants = [ultimate_parent] + ultimate_parent.children_recursive

            # Calculate center of mass.
            meshes = [
                convert_blender_object_to_trimesh(descendant)
                for descendant in descendants
            ]
            joined_mesh = trimesh.util.concatenate(meshes)
            center_of_mass = joined_mesh.center_mass
            del joined_mesh, meshes

            # Create a (rigid body, compound parent) center of mass object (sphere) with
            # the center of mass and the mass of the agglomerate.

            # Set the particle collection as the active collection
            bpy.context.view_layer.active_layer_collection = (
                bpy.context.view_layer.layer_collection.children["Particles"])

            bpy.ops.mesh.primitive_ico_sphere_add(location=center_of_mass)
            center_of_mass_object = bpy.context.active_object

            center_of_mass_objects.append(center_of_mass_object)

            center_of_mass_object.name = "Center of mass"
            center_of_mass_object.hide_render = True
            set_rigidity(center_of_mass_object, True)

            # TODO: Use a more dynamic way to set the mass (e.g. by calculating it
            # based on the volume of the agglomerate or using a custom property.).

            # Set rigid body properties for center of mass object.
            center_of_mass_object.rigid_body.mass = self.mass
            center_of_mass_object.rigid_body.collision_shape = "COMPOUND"
            center_of_mass_object.rigid_body.angular_damping = self.angular_damping
            center_of_mass_object.rigid_body.linear_damping = self.linear_damping
            center_of_mass_object.rigid_body.use_margin = self.collision_margin > 0
            center_of_mass_object.rigid_body.collision_margin = self.collision_margin
            center_of_mass_object.rigid_body.friction = self.friction
            center_of_mass_object.rigid_body.restitution = self.restitution

            # Iterate all descendants and set their parent attribute to the center of
            # mass object.
            for descendant in descendants:
                # Un-parent object and reset its position to clear potentially existing
                # transformations.
                # TODO: Include this functionality in the utilities.parent function.
                original_transformation = descendant.matrix_world.copy()
                descendant.parent = None
                descendant.matrix_world = original_transformation

                select_only(descendant)
                set_parent(descendant, center_of_mass_object, keep_transform=True)

                # Set rigid body properties for descendants.
                set_rigidity(descendant, True)
                descendant.rigid_body.mass = self.mass
                descendant.rigid_body.collision_shape = self.collision_shape.upper()
                descendant.rigid_body.mesh_source = self.mesh_source.upper()
                descendant.rigid_body.angular_damping = self.angular_damping
                descendant.rigid_body.linear_damping = self.linear_damping
                descendant.rigid_body.use_margin = self.collision_margin > 0
                descendant.rigid_body.collision_margin = self.collision_margin
                descendant.rigid_body.friction = self.friction
                descendant.rigid_body.restitution = self.restitution

        # Bake the physics simulation.
        scene.frame_end = self.num_frames
        scene.rigidbody_world.point_cache.frame_end = self.num_frames
        bpy.ops.ptcache.free_bake_all()
        bpy.ops.ptcache.bake_all(bake=True)
        scene.frame_set(self.num_frames)

        # Restore original names.
        for new_name, old_name in renaming_mapping.items():
            bpy.data.objects[new_name].name = old_name

        if not self.dry_run:
            # Save the new positions and rotations. We need to copy the transforms, so
            # that they are decoupled from Blender, because, when we load the original
            # state, that will break references.
            new_transforms: dict[str, np.ndarray] = {}

            # We need a quite complicated way to get all affected particles, because the
            # conversion to meshes broke the references.
            for center_of_mass_object in center_of_mass_objects:
                for child in center_of_mass_object.children:
                    new_transforms[child.name] = child.matrix_world.copy()

            # Restore original state.
            original_state.load_from_disk()
            runtime_state = original_state.runtime_state
            original_state.delete()

            # Apply the transforms to the original scene. We need to apply the
            # transforms recursively, because else, the children are moved multiple
            # times.
            affected_particle_objects = [
                particle.blender_object for particle in self.affected_set()
            ]

            ultimate_parents = [
                blender_object for blender_object in affected_particle_objects
                if blender_object.parent is None
            ]

            for ultimate_parent in ultimate_parents:
                _apply_transforms_recursively(ultimate_parent, new_transforms)

        else:
            # If we are in dry run mode, we save the state to a file and abort the run.
            # We do this because we changed the scene drastically, which would probably
            # break the rest of the recipe.
            SaveState("dry_run")(runtime_state)
            raise RuntimeWarning(
                "Dry run finished. Saved state to 'dry_run.blend'. And aborting the"
                " rest of the recipe. Set dry_run to False to fully run the recipe.")

        return runtime_state


def _apply_transforms_recursively(blender_object: bpy.types.Object,
                                  transforms: dict[str, mathutils.Matrix]) -> None:
    """Recursively apply a transform to a Blender object and all its children.

    Args:
        blender_object (bpy.types.Object): Blender object to apply the transform to.
        transform (np.ndarray): Transform to apply.
    """
    blender_object.matrix_world = transforms[blender_object.name]

    for child in blender_object.children:
        _apply_transforms_recursively(child, transforms)
