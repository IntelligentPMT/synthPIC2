"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import pathlib
import sys
from typing import List

PROJECT_ROOT = pathlib.Path(__file__).parents[2].resolve().as_posix()
sys.path.insert(0, PROJECT_ROOT)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "synthPIC2"
copyright = "2024, Max Frei, Robert Panckow, Felix Febrian, Xuebei Zhu"    #pylint: disable=redefined-builtin
author = "Max Frei, Robert Panckow, Felix Febrian, Xuebei Zhu"
release = "0.5dev"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration", "sphinx.ext.autodoc", "sphinx.ext.autosummary",
    "sphinx_copybutton"
]

templates_path = ["_templates"]
exclude_patterns: List[str] = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

# -- Mock imports ------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports

autodoc_mock_imports = ["bpy", "hydra", "omegaconf", "wandb"]
