"""Module for the `FeatureGenerationStep` base class."""

import attr

from ..step import SynthChainStep


@attr.s(auto_attribs=True)
class RenderingStep(SynthChainStep):
    pass
