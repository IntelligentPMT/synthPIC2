"""Module for recipe utilities."""

import re

import omegaconf

from .recipe import Recipe


def parse_recipe(recipe: Recipe) -> None:
    """Parse builtin namespace placeholder in recipe and infer item names from
        dictionary keys.

    Args:
        recipe (Recipe): Recipe to parse.
    """

    infer_names(recipe)
    parse_builtin_namespaces(recipe)
    parse_plugin_namespaces(recipe)


def parse_plugin_namespaces(recipe: Recipe) -> None:
    """Parse plugin namespace placeholder in recipe.

    Uses the following regex: https://regex101.com/r/gVHrlX/1

    Args:
        recipe (Recipe): Recipe to parse.
    """

    regex = r"\$plugins\.(\w+)\.(.+)"

    feature_criteria_node = recipe.process_conditions.feature_criteria
    if feature_criteria_node is not None:
        node_namespace = "process_conditions.feature_criteria."
        substitution = f"plugins.\\1.{node_namespace}\\2"
        for node in feature_criteria_node.values():
            node["_target_"] = re.sub(regex, substitution, node["_target_"], 1)

    feature_variabilities_node = recipe.process_conditions.feature_variabilities

    if feature_variabilities_node is not None:
        node_namespace = "process_conditions.variabilities."
        substitution = f"plugins.\\1.{node_namespace}\\2"
        for node in feature_variabilities_node.values():

            node.variability["_target_"] = re.sub(regex, substitution,
                                                  node.variability["_target_"], 1)

    node_namespace = "synth_chain.feature_generation_steps."
    substitution = f"plugins.\\1.{node_namespace}\\2"
    for node in recipe.synth_chain.feature_generation_steps:
        node["_target_"] = re.sub(regex, substitution, node["_target_"], 1)

    node_namespace = "synth_chain.rendering_steps."
    substitution = f"plugins.\\1.{node_namespace}\\2"
    for node in recipe.synth_chain.rendering_steps:
        node["_target_"] = re.sub(regex, substitution, node["_target_"], 1)


def parse_builtin_namespaces(recipe: Recipe) -> None:
    """Parse builtin namespace placeholder in recipe.

    Args:
        recipe (Recipe): Recipe to parse.
    """

    builtins_placeholder = "$builtins"

    feature_criteria_node = recipe.process_conditions.feature_criteria

    if feature_criteria_node is not None:
        for node in feature_criteria_node.values():
            node["_target_"] = node["_target_"].replace(
                f"{builtins_placeholder}.",
                "synthpic2.recipe.process_conditions.feature_criteria.")

    feature_variabilities_node = recipe.process_conditions.feature_variabilities

    if feature_variabilities_node is not None:
        for node in feature_variabilities_node.values():
            node.variability["_target_"] = node.variability["_target_"].replace(
                f"{builtins_placeholder}.",
                "synthpic2.recipe.process_conditions.variabilities.")

    for node in recipe.synth_chain.feature_generation_steps:
        node["_target_"] = node["_target_"].replace(
            f"{builtins_placeholder}.",
            "synthpic2.recipe.synth_chain.feature_generation_steps.")

    for node in recipe.synth_chain.rendering_steps:
        node["_target_"] = node["_target_"].replace(
            f"{builtins_placeholder}.", "synthpic2.recipe.synth_chain.rendering_steps.")


def infer_names(recipe: Recipe) -> None:
    """Iterate certain nodes of the recipe and set the name attribute of the node items
    to the key that was used for the item in the recipe.

    Args:
        recipe (Recipe): Recipe to parse.
    """

    nodes_to_parse = [
        recipe.blueprints.measurement_techniques,
        recipe.blueprints.particles,
        recipe.process_conditions.feature_criteria,
        recipe.process_conditions.sets,
        recipe.process_conditions.feature_variabilities,
    ]

    for node in nodes_to_parse:
        if node is not None:
            assert isinstance(node, omegaconf.DictConfig)
            _infer_item_names_from_keys(node)


def _infer_item_names_from_keys(node: omegaconf.DictConfig) -> None:
    if node is not None:
        for key, value in node.items():
            assert isinstance(value, omegaconf.Container)
            with omegaconf.open_dict(value):
                value["name"] = key
