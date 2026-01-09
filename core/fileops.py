import os
import json
import hashlib
from datetime import datetime

# Base directory for all scan results
# All tool outputs and reports are stored here
from core.config import ConfigManager

# Base directory for all scan results
# All tool outputs and reports are stored here
DEFAULT_OUTPUT_DIR = "/tmp/Vajra-results"

# Shim for legacy tools
RESULT_BASE = str(ConfigManager.get_output_dir())




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
        base_dir = os.path.join(ConfigManager.get_output_dir(), group_name, combined_name)
    else:
        # For single targets
        base_dir = os.path.join(ConfigManager.get_output_dir(), combined_name)

    # Create Logs, Reports, JSON sub-folders
    for folder in ("Logs", "Reports", "JSON"):
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    return base_dir


# Simple caching system for expensive operations
_cache_dir = None
_cache_enabled = True

def get_cache_dir():
    """Get cache directory path."""
    global _cache_dir
    if _cache_dir is None:
        _cache_dir = os.path.join(ConfigManager.get_output_dir(), ".cache")
        os.makedirs(_cache_dir, exist_ok=True)
    return _cache_dir

def get_cache_key(data):
    """Generate cache key from data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif isinstance(data, dict):
        data = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(data).hexdigest()

def get_cached_result(cache_key, max_age_hours=24):
    """Get cached result if it exists and is not too old."""
    if not _cache_enabled:
        return None

    cache_file = os.path.join(get_cache_dir(), f"{cache_key}.json")
    if not os.path.exists(cache_file):
        return None

    try:
        # Check if cache is too old
        if max_age_hours > 0:
            mtime = os.path.getmtime(cache_file)
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            if age_hours > max_age_hours:
                os.unlink(cache_file)
                return None

        with open(cache_file, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

def set_cached_result(cache_key, data):
    """Cache result data."""
    if not _cache_enabled:
        return

    try:
        cache_file = os.path.join(get_cache_dir(), f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # Silently fail if caching fails

def clear_cache():
    """Clear all cached results."""
    try:
        cache_dir = get_cache_dir()
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                os.unlink(os.path.join(cache_dir, filename))
    except OSError:
        pass
