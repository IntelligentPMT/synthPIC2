"""Module for SynthChainSteps."""

from abc import abstractmethod
from pathlib import Path
from typing import Callable, Optional

import attr
import bpy
from matplotlib.colors import hex2color
from matplotlib.colors import rgb2hex
import pandas as pd

from ....blender import Gpu
from ....blender import utilities as blender
from ....blender.utilities import assign_material
from ....blender.utilities import create_emission_shader
from ....blender.utilities import deselect_all
from ....custom_types import AnyPath
from ....utilities import get_unique_reproducible_random_colors
from ...blueprints import Particle
from ...process_conditions.sets import Set
from ...prototypes.feature import Feature
from ...registries import SET_REGISTRY
from ...registries.registries import MEASUREMENT_TECHNIQUE_REGISTRY
from ...render_preparation_mixin import RenderPreparationMixin
from ..state import RuntimeState
from ..state import State
from .base import RenderingStep


class _Renderer(RenderPreparationMixin):
    """Class to control the rendering method (e.g. image or stl)."""

    def __init__(self) -> None:
        self.render: Callable[[AnyPath], None] = self.render_image_to_file
        self.hide_object: Callable[[bpy.types.Object], None] = self.hide_in_render
        self.show_object: Callable[[bpy.types.Object], None] = self.show_in_render

    @staticmethod
    def select(object_: bpy.types.Object) -> None:
        blender.select(object_)

    @staticmethod
    def deselect(object_: bpy.types.Object) -> None:
        blender.deselect(object_)

    @staticmethod
    def render_image_to_file(output_path: AnyPath) -> None:
        blender.render_to_file(output_path)

    @staticmethod
    def export_stl_to_file(output_path: AnyPath) -> None:
        # Force stl file extension.
        output_path = Path(output_path).with_suffix(".stl")
        blender.export_selected_objects_as_stl(output_path)

    @staticmethod
    def hide_in_render(object_: bpy.types.Object) -> None:
        blender.hide_in_render(object_)

    @staticmethod
    def show_in_render(object_: bpy.types.Object) -> None:
        blender.show_in_render(object_)

    def _prepare_stl_rendering_mode(self) -> None:
        self.render = self.export_stl_to_file
        self.hide_object = self.deselect
        self.show_object = self.select


class _Scene(RenderPreparationMixin):
    """Class to control the preparation of the scene (i.e. everything but the particles)
        for the different rendering steps."""

    @staticmethod
    def _prepare_real_rendering_mode() -> None:
        Gpu.enable()

    @staticmethod
    def _prepare_stl_rendering_mode() -> None:
        deselect_all()

    def _prepare_stylized_rendering_mode(self) -> None:

        self._setup_accurate_colors()
        self._disable_compositing()

        scene = bpy.data.scenes[0]

        render_settings = scene.render
        render_settings.engine = "BLENDER_WORKBENCH"
        render_settings.use_high_quality_normals = True

        image_settings = render_settings.image_settings
        image_settings.color_mode = "BW"
        image_settings.color_depth = "8"

        shading = scene.display.shading

        shading.color_type = "SINGLE"
        shading.single_color = (1, 1, 1)
        shading.show_specular_highlight = False
        shading.show_object_outline = True
        shading.object_outline_color = (0, 0, 0)
        shading.show_backface_culling = False
        shading.show_xray = False
        shading.show_shadows = False
        shading.show_cavity = False
        shading.use_dof = False

    def _prepare_stylized_xray_rendering_mode(self) -> None:
        self._prepare_stylized_rendering_mode()
        shading = bpy.data.scenes[0].display.shading
        shading.show_xray = True
        shading.xray_alpha = 0.5

    def _prepare_normal_map_rendering_mode(self) -> None:

        scene = bpy.data.scenes[0]

        render_settings = scene.render
        render_settings.engine = "BLENDER_EEVEE"
        scene.eevee.taa_render_samples = 1
        render_settings.use_compositing = True

        image_settings = render_settings.image_settings
        image_settings.color_mode = "RGB"
        image_settings.color_depth = "8"
        self._setup_accurate_colors()

        scene.view_layers[0].use_pass_normal = True

        scene.use_nodes = True

        self._delete_compositing_nodes()
        compositing_nodes = scene.node_tree.nodes
        render_layer_node = compositing_nodes.new("CompositorNodeRLayers")
        composite_node = compositing_nodes.new("CompositorNodeComposite")

        links = scene.node_tree.links
        links.new(render_layer_node.outputs["Normal"], composite_node.inputs["Image"])

    def _prepare_depth_map_rendering_mode(self) -> None:

        scene = bpy.data.scenes[0]

        render_settings = scene.render
        render_settings.engine = "BLENDER_EEVEE"
        scene.eevee.taa_render_samples = 1
        render_settings.use_compositing = True

        image_settings = render_settings.image_settings
        image_settings.color_mode = "BW"
        image_settings.color_depth = "8"
        self._setup_accurate_colors()

        scene.view_layers[0].use_pass_z = True

        scene.use_nodes = True

        self._delete_compositing_nodes()
        compositing_nodes = scene.node_tree.nodes

        render_layer_node = compositing_nodes.new("CompositorNodeRLayers")

        less_than_node = compositing_nodes.new("CompositorNodeMath")
        less_than_node.operation = "LESS_THAN"
        less_than_node.inputs[1].default_value = 3.40282e+38

        set_alpha_node = compositing_nodes.new("CompositorNodeSetAlpha")
        normalize_node = compositing_nodes.new("CompositorNodeNormalize")
        composite_node = compositing_nodes.new("CompositorNodeComposite")

        links = scene.node_tree.links
        links.new(render_layer_node.outputs["Depth"], less_than_node.inputs[0])
        links.new(render_layer_node.outputs["Depth"], set_alpha_node.inputs["Image"])
        links.new(less_than_node.outputs["Value"], set_alpha_node.inputs["Alpha"])
        links.new(set_alpha_node.outputs["Image"], normalize_node.inputs["Value"])
        links.new(normalize_node.outputs["Value"], composite_node.inputs["Image"])

    @staticmethod
    def _prepare_categorical_rendering_mode() -> None:
        Gpu.disable()

        scene = bpy.data.scenes[0]

        render_settings = scene.render
        render_settings.engine = "CYCLES"
        render_settings.use_compositing = False

        cycles = scene.cycles
        cycles.samples = 1
        cycles.use_denoising = False

        image_settings = render_settings.image_settings
        image_settings.color_mode = "RGB"
        image_settings.color_depth = "8"

        _Scene._setup_accurate_colors()

        _Scene._disable_depth_of_field()
        _Scene._disable_lights()
        _Scene._disable_emission()
        _Scene._disable_world()

    @staticmethod
    def _setup_accurate_colors() -> None:
        scene = bpy.data.scenes[0]

        render_settings = scene.render
        render_settings.dither_intensity = 0

        image_settings = render_settings.image_settings
        image_settings.compression = 100

        scene.display_settings.display_device = "sRGB"
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        scene.display_settings.display_device = "None"
        scene.view_settings.exposure = 0
        scene.view_settings.gamma = 1
        scene.sequencer_colorspace_settings.name = "Raw"

    @staticmethod
    def _disable_depth_of_field() -> None:
        for camera in bpy.data.cameras:
            camera.dof.use_dof = False

    @staticmethod
    def _disable_world() -> None:
        for world in bpy.data.worlds:
            bpy.data.worlds.remove(world)

    @staticmethod
    def _disable_emission() -> None:
        for material in bpy.data.materials:
            if material.node_tree is not None:
                for node in material.node_tree.nodes:
                    if "Emission Strength" in node.inputs:
                        node.inputs["Emission Strength"].default_value = 0

                    if node.type == "EMISSION":
                        node.inputs["Strength"].default_value = 0

    @staticmethod
    def _disable_lights() -> None:
        for object_ in bpy.data.objects:
            if object_.type == "LIGHT":
                object_.hide_render = True

    @staticmethod
    def _disable_compositing() -> None:
        bpy.data.scenes[0].render.use_compositing = False

    @staticmethod
    def _delete_compositing_nodes() -> None:
        scene = bpy.data.scenes[0]
        scene.use_nodes = True
        compositing_nodes = scene.node_tree.nodes
        for node in compositing_nodes:
            compositing_nodes.remove(node)


@attr.s(auto_attribs=True)
class _Particles(RenderPreparationMixin):
    """Class to control the preparation of the particles for the different rendering
        steps."""
    set_of_interest: Set
    set_overlapping: Set

    def prepare_for_render(self, rendering_mode: str) -> None:
        self.particles_all = SET_REGISTRY["AllParticles"]()    #pylint: disable=not-callable
        self.particles_of_interest = self.set_of_interest()
        self.particles_overlapping = self.set_overlapping()

        # Hide all particles.
        for particle in self.particles_all:
            particle.blender_object.hide_render = True

        # Assign unique random category_colors to particles.
        num_particles = len(self.particles_all)
        colors = get_unique_reproducible_random_colors(num_particles)

        for particle, color in zip(self.particles_all, colors):
            color_hex = rgb2hex(color)    # type: ignore

            if "category_color" in particle.features:
                particle.features["category_color"].value = color_hex
            else:
                particle.features.register(
                    Feature(name="category_color", _value=color_hex))

        super().prepare_for_render(rendering_mode)

    def _prepare_categorical_rendering_mode(self) -> None:
        for particle in self.particles_all:
            color_hex = particle.features.query("category_color", strict=True).value
            color = hex2color(color_hex) + (1,)

            emission_shader = create_emission_shader(color=color)
            assign_material(
                particle.blender_object,
                emission_shader.name,
            )

        for particle in self.particles_overlapping:
            if particle not in self.particles_of_interest:
                emission_shader = create_emission_shader(color=(0, 0, 0, 1))
                assert isinstance(particle, Particle)
                assign_material(
                    particle.blender_object,
                    emission_shader.name,
                )

    def _prepare_real_rendering_mode(self) -> None:
        for particle in self.particles_overlapping:
            if particle not in self.particles_of_interest:
                assert isinstance(particle, Particle)
                particle.blender_object.visible_camera = False


@attr.s(auto_attribs=True)
class ParametricRenderingStep(RenderingStep):
    pass


@attr.s(auto_attribs=True)
class DiscreteRenderingStep(RenderingStep):
    """Prepare and render the current scene."""
    rendering_mode: str
    output_file_name_prefix: str = ""
    set_name_of_interest: str = "AllParticles"
    set_name_overlapping: Optional[str] = "Empty"
    subfolder: Optional[str] = None

    do_save_features: bool = False
    do_save_state: bool = False
    image_file_extension: str = "png"

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        self.set_of_interest = SET_REGISTRY.query(self.set_name_of_interest,
                                                  strict=True)

        if self.set_name_overlapping is None or self.rendering_mode.lower() == "stl":
            self.set_name_overlapping = "Empty"

        self.set_overlapping = SET_REGISTRY.query(self.set_name_overlapping,
                                                  strict=True)

    def save_features(self) -> None:

        self.save_particle_features()
        self.save_measurement_technique_features()

    def save_particle_features(self) -> None:
        csv_path = self.output_folder_path / "particle_features.csv"
        particles = SET_REGISTRY["AllParticles"]()    #pylint: disable=not-callable
        features = pd.DataFrame(data=[
            pd.Series(name=particle.md5,
                      data=[feature.value
                            for feature in particle.features],
                      index=[feature.name
                             for feature in particle.features])
            for particle in particles
        ])
        features.index.name = "Particle hash"
        features.to_csv(csv_path)

    def save_measurement_technique_features(self) -> None:
        csv_path = (self.output_folder_path / "measurement_technique_features.csv")
        measurement_technique = MEASUREMENT_TECHNIQUE_REGISTRY[0]

        # Gather features, but ignore features that are no longer available (e.g. due to
        # the Blender `world` object having been deleted).
        feature_names = []
        feature_values = []

        for feature in measurement_technique.features:
            try:
                feature_values.append(feature.value)
                feature_names.append(feature.name)
            except KeyError:
                pass

        features = pd.DataFrame(data=pd.Series(
            name="Measurement Technique", data=feature_values, index=feature_names))
        features.index.name = "Features"
        features.to_csv(csv_path, header=False)

    def __call__(self, runtime_state: RuntimeState) -> RuntimeState:
        # Use the fact, that there is only a single measurement technique.
        measurement_technique = MEASUREMENT_TECHNIQUE_REGISTRY[0]

        self.output_root = Path(measurement_technique.features["output_root"].value)

        self.output_folder_path = self.output_root / self.rendering_mode

        if self.subfolder is not None:
            self.output_folder_path /= self.subfolder

        self.output_folder_path.mkdir(parents=True, exist_ok=True)

        # Save original state
        original_state = State(runtime_state=runtime_state)
        original_state.save_to_disk()

        measurement_technique.prepare_for_render(self.rendering_mode)

        _Scene().prepare_for_render(self.rendering_mode)
        _Particles(set_of_interest=self.set_of_interest,
                   set_overlapping=self.set_overlapping).prepare_for_render(
                       self.rendering_mode)
        self.renderer = _Renderer()
        self.renderer.prepare_for_render(self.rendering_mode)

        self.set_descriptor = f"{self.set_overlapping.md5}_over_{self.set_of_interest.md5}"    #pylint: disable=line-too-long

        self.set_info_root = self.output_root / "set_info"
        self.set_info_root.mkdir(parents=True, exist_ok=True)

        self.save_set_info()

        if self.do_save_state:
            save_state = State(name=self.set_descriptor,
                               runtime_state=runtime_state,
                               file_root=self.output_folder_path)
            save_state.save_to_disk()
            save_state.unregister()

        self.render()

        if self.do_save_features:
            self.save_features()

        # Restore original state.
        original_state.load_from_disk()
        runtime_state = original_state.runtime_state
        original_state.delete()

        return runtime_state

    def save_set_info(self) -> None:
        self._save_set_hashes()
        self._save_particle_set_associations()

    def _save_particle_set_associations(self) -> None:
        sets = [self.set_of_interest, self.set_overlapping]

        for set_ in sets:
            set_info_file_path = self.set_info_root / f"{set_.name}_{set_.md5}.txt"

            if set_info_file_path.exists():
                continue

            with open(set_info_file_path, mode="a", encoding="utf-8") as file:
                for particle in set_():
                    file.write(particle.md5 + "\n")

    def _save_set_hashes(self) -> None:
        set_info_file_path = self.set_info_root / "set_hashes.csv"

        if set_info_file_path.exists():
            set_info_old = pd.read_csv(set_info_file_path)
        else:
            set_info_old = pd.DataFrame()

        set_hashes = pd.Series(
            name="set_hash", data=[self.set_of_interest.md5, self.set_overlapping.md5])

        set_names = pd.Series(
            name="set_name",
            data=[self.set_of_interest.name, self.set_overlapping.name])

        set_info_new = pd.concat([set_hashes, set_names], axis=1)

        set_info = pd.concat([set_info_old, set_info_new]).drop_duplicates()

        set_info.to_csv(set_info_file_path, index=False)

    @abstractmethod
    def render(self) -> None:
        pass


@attr.s(auto_attribs=True)
class RenderParticlesIndividually(DiscreteRenderingStep):
    """Class to render a whole set of particles into a single image."""

    def render(self) -> None:
        for particle in self.set_of_interest():
            self.renderer.show_object(particle.blender_object)

            file_name = f"{self.output_file_name_prefix}{particle.md5}.{self.image_file_extension}"    #pylint: disable=line-too-long
            file_path = self.output_folder_path / file_name
            self.renderer.render(file_path)

            self.renderer.hide_object(particle.blender_object)


@attr.s(auto_attribs=True)
class RenderParticlesTogether(DiscreteRenderingStep):
    """Class to render a whole set of particles into a single image."""

    def render(self) -> None:
        for particle in self.set_of_interest():
            self.renderer.show_object(particle.blender_object)

        for particle in self.set_overlapping():
            self.renderer.show_object(particle.blender_object)

        file_name = f"{self.output_file_name_prefix}{self.set_descriptor}.{self.image_file_extension}"    #pylint: disable=line-too-long
        file_path = self.output_folder_path / file_name
        self.renderer.render(file_path)
