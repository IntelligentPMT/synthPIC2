"""Definition of the structure of the image synthesis Recipe class."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any, Dict, List, Optional

import attr
from omegaconf import MISSING

from ..utilities import get_object_md5
from .blueprints.blueprints import MeasurementTechniqueBlueprint
from .blueprints.blueprints import ParticleBlueprint
from .process_conditions.feature_variability import FeatureVariability
from .process_conditions.sets import Set
from .synth_chain import SynthChain
from .synth_chain.state import RuntimeState


@attr.s(auto_attribs=True)
class Blueprints:
    _convert_: str = "all"
    measurement_techniques: Dict[str, MeasurementTechniqueBlueprint] = MISSING
    particles: Optional[Dict[str, ParticleBlueprint]] = None


@attr.s(auto_attribs=True)
class ProcessConditions:
    # TODO: Add validation of `feature_criteria` (and check if hydra can do this).
    _convert_: str = "all"
    feature_criteria: Optional[Dict[str, Any]] = None
    sets: Optional[Dict[str, Set]] = None
    feature_variabilities: Optional[Dict[str, FeatureVariability]] = None


HELP_TEMPLATE = """
${hydra.help.header}

== Config ==

Override anything in the config (foo.bar=value)


$CONFIG


${hydra.help.footer}
"""


@dataclass    #`attr.s` won't work, because of `field` command.
class Recipe:
    """Definition of the structure of the Recipe class."""
    _target_: str = "synthpic2.Recipe"
    _convert_: str = "all"

    defaults: List[Any] = field(default_factory=lambda: [{
        "override hydra/launcher": "joblib"
    }])

    hydra: Any = field(
        default_factory=lambda: {
            "run": {
                "dir": "output/${hydra.job.config_name}/${now:%Y-%m-%d_%H-%M-%S}/run0"
            },
            "sweep": {
                "dir": "output/${hydra.job.config_name}/${now:%Y-%m-%d_%H-%M-%S}",
                "subdir": "run${hydra.job.num}"
            },
            "job": {
                "name": "synthPIC2"
            },
            "help": {
                "header": "${hydra.help.app_name} help:\n",
                "template": HELP_TEMPLATE
            },
            "launcher": {
                "n_jobs": 2,
                "batch_size": 1
            },
            "sweeper": {
                "max_batch_size": 1,
            },
        })
    initial_runtime_state: RuntimeState = RuntimeState()
    blueprints: Blueprints = Blueprints()
    process_conditions: ProcessConditions = ProcessConditions()
    synth_chain: SynthChain = SynthChain()

    @property
    def md5(self) -> str:
        return get_object_md5(self)

    def execute(self) -> None:
        self.synth_chain.execute(self.initial_runtime_state)
