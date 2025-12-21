"""
VAJRA File Operations Utility
Directory and file handling for scan results
"""

import os
from datetime import datetime

RESULT_BASE = "/tmp/Vajra-results"


def get_group_name_from_file(file_path: str) -> str:
    file_name = os.path.basename(file_path)
    return os.path.splitext(file_name)[0]


def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def create_target_dirs(target: str, group_name: str | None = None) -> str:
    """
    Creates timestamped directory structure.

    Single target:
    /tmp/Vajra-results/<target>/<timestamp>/

    File input:
    /tmp/Vajra-results/<group>/<target>/<timestamp>/
    """

    if not target:
        raise ValueError("Target cannot be empty")

    timestamp = get_timestamp()

    if group_name:
        base_dir = os.path.join(RESULT_BASE, group_name, target, timestamp)
    else:
        base_dir = os.path.join(RESULT_BASE, target, timestamp)

    for folder in ("Logs", "Reports", "JSON"):
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    return base_dir
