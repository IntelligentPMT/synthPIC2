#!/usr/bin/env python3
"""
Based on: https://gist.github.com/crhan/4d45c28015f2046704cedb67a80d3cec
Reason: see
    https://github.com/microsoft/vscode-remote-release/issues/512#issuecomment-1100774534
"""

import hashlib
import logging
import os
from pathlib import Path
import time

logging.basicConfig(
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

_LOGGER = logging.getLogger(__name__)


def get_cwd() -> Path:
    return Path(os.path.abspath(__file__)).parent


def get_project_name() -> str:
    """Generate a unique project name."""
    project_dir_name = get_cwd().parent.name
    user_name = os.getlogin()
    post_fix = get_random_hash()[:8]
    # VSCode does not allow capital letters in the project name.
    project_name = f"{project_dir_name}_{user_name}_{post_fix}".lower()
    _LOGGER.info("project_name: %s", project_name)
    return project_name


def get_random_hash() -> str:
    return hashlib.sha1(str(time.time()).encode("utf-8")).hexdigest()


def write_project_name_to_dotenv(dotenv_path: Path) -> None:
    """
    Write the `COMPOSE_PROJECT_NAME` to the `.env` file, if it is not already present.
    """
    was_already_initialized = False

    dotenv_path.parent.mkdir(exist_ok=True, parents=True)

    if not dotenv_path.exists():
        dotenv_path.touch()

    lines = open(dotenv_path, "r", encoding="utf-8").readlines()
    with open(dotenv_path, "a", encoding="utf-8") as wf:
        for line in lines:
            if line.startswith("COMPOSE_PROJECT_NAME="):
                was_already_initialized = True
                _LOGGER.info("Already initialized")

        if not was_already_initialized:
            project_name = get_project_name()
            wf.write("\n# Automatically added: Unique project name, to prevent docker"
                     "container name conflicts for multi-user hosts.")
            wf.write(f"\nCOMPOSE_PROJECT_NAME={project_name}\n")
            _LOGGER.info("Initialized")


def main() -> None:
    cwd = get_cwd()
    write_project_name_to_dotenv(cwd.parent / ".env")


if __name__ == "__main__":
    main()
