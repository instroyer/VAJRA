import os
import re


def normalize_target(target: str) -> str:
    """
    Normalize target by removing protocol only.
    Path is preserved.
    """

    target = target.strip()

    # Remove protocol (keep path)
    target = re.sub(r"^https?://", "", target, flags=re.IGNORECASE)

    return target


def parse_targets(input_value: str):
    """
    Parse single target or file containing targets.

    Returns:
        targets (list[str])
        source_type (str): "single" | "file"
    """

    if not input_value:
        raise ValueError("Empty target input")

    targets = []

    if os.path.isfile(input_value):
        with open(input_value, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                normalized = normalize_target(line)
                if normalized:
                    targets.append(normalized)
        return targets, "file"

    # Single target
    return [normalize_target(input_value)], "single"
