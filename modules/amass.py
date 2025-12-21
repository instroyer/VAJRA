# VAJRA/Modules/amass.py
# Amass module execution
import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Engine.logger import info, error

def run(target, output_dir):
    """Run the amass tool on the target."""
    try:
        log_file = f"{output_dir}/Logs/amass.txt"
        
       
        command = f"amass enum -d {target} -o {log_file}"
        info(f"Running: {command}")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                with open(log_file, 'r') as f:
                    line_count = len(f.readlines())
                info(f"Amass found {line_count} subdomains. Saved to: {log_file}")
                return True
            else:
                info("Amass completed but found no subdomains")
                return True
        else:
            error(f"Amass failed: {result.stderr[:200]}...")
            return False

    except Exception as e:
        error(f"Error executing amass: {e}")
        return False
