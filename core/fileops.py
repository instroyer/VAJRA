import os
from datetime import datetime

# Base directory for all scan results
# All tool outputs and reports are stored here
RESULT_BASE = "/tmp/Vajra-results"


def get_group_name_from_file(file_path: str) -> str:
    """
    Returns filename without extension.
    Example: targets.txt -> targets
    """
    if not file_path:
        return "default"
    file_name = os.path.basename(file_path)
    return os.path.splitext(file_name)[0]


def get_timestamp() -> str:
    return datetime.now().strftime("%d%m%Y_%H%M%S")


def create_target_dirs(target: str, group_name: str | None = None) -> str:
    """
    Creates combined target-timestamped directory structure.

    Single target:
    /tmp/Vajra-results/<target>_<timestamp>/

    File input:
    /tmp/Vajra-results/<group>/<target>_<timestamp>/
    """

    if not target:
        raise ValueError("Target cannot be empty")

    timestamp = get_timestamp()
    combined_name = f"{target}_{timestamp}"

    if group_name:
        # For file inputs, place it inside the group folder
        base_dir = os.path.join(RESULT_BASE, group_name, combined_name)
    else:
        # For single targets
        base_dir = os.path.join(RESULT_BASE, combined_name)

    # Create Logs, Reports, JSON sub-folders
    for folder in ("Logs", "Reports", "JSON"):
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    return base_dir
