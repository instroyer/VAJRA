# VAJRA/Modules/httpx.py
# Description: HTTPX module execution (using httpx-toolkit).

import subprocess
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Engine.logger import info, success, error

def extract_urls_from_json(json_file, output_file):
    """Extract clean URLs from httpx JSON output using jq and sed."""
    try:
        command = f"jq -r '.url' {json_file} | sed -E 's#(https?://)?([^/]+).*#\\2#' | sort -u > {output_file}"
        info(f"Extracting unique hostnames from JSON output...")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            with open(output_file, 'r') as f:
                url_count = len(f.readlines())
            success(f"Extracted {url_count} unique hostnames to: {os.path.basename(output_file)}")
            return True
        else:
            error(f"URL extraction failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        error(f"Error extracting URLs from JSON: {e}")
        return False

def run(target, output_dir):
    """Run the httpx-toolkit on the target and extract clean hostnames."""
    json_output = os.path.join(output_dir, "Logs", "alive.json")
    txt_output = os.path.join(output_dir, "Logs", "alive.txt")
    command = ""

    try:
        # --- CHANGE START: Logic to handle different input types ---
        if target.startswith('@'):
            # Input is a file list (e.g., from merged_subs.txt or a user file)
            input_file = target[1:]
            if not os.path.exists(input_file) or os.path.getsize(input_file) == 0:
                error(f"Input file not found or is empty: {input_file}. Skipping HTTPX.")
                return False
            command = f"cat {input_file} | httpx-toolkit -json -o {json_output}"
        else:
            # Input is a single domain/IP
            command = f"echo {target} | httpx-toolkit -json -o {json_output}"
       

        info(f"Running: {command}")
        # Using a longer timeout for potentially large lists
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            if not os.path.exists(json_output) or os.path.getsize(json_output) == 0:
                warning("HTTPX ran successfully but found no live hosts.")
                return True # Not a failure, just no results
            
            success(f"HTTPX JSON results saved to: {os.path.basename(json_output)}")
            
            if extract_urls_from_json(json_output, txt_output):
                info("Clean hostnames for other tools are available in alive.txt.")
                return True
            else:
                error("HTTPX succeeded but hostname extraction failed.")
                return False
        else:
            error(f"HTTPX failed: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        error("HTTPX timed out after 5 minutes. Skipping.")
        return False
    except Exception as e:
        error(f"An error occurred while executing httpx-toolkit: {e}")
        return False
