# Subfinder module execution
import subprocess
from Engine.logger import info, error

def run(target, output_dir):
    """Run the subfinder tool on the target."""
    try:
        log_file = f"{output_dir}/Logs/subfinder.txt"
        command = f"subfinder -d {target} -silent -o {log_file}"
        
        info(f"Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            info(f"Subfinder results saved to: {log_file}")
            return True
        else:
            error(f"Subfinder failed: {result.stderr}")
            return False
    except Exception as e:
        error(f"Error executing subfinder: {e}")
        return False
