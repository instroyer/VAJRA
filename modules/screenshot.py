# Modules/screenshot.py

# Screenshot (Eyewitness) module execution
import subprocess
import os
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Engine.logger import info, error

def run(target, output_dir, report_enabled=False):
    """Run the eyewitness tool on the target."""
    try:
        # Handle file input (@filename.txt)
        if target.startswith('@'):
            file_path = target[1:] 
            if not os.path.isfile(file_path):
                error(f"File not found: {file_path}")
                return False
            
            command = f"eyewitness --web --timeout 30 --threads 500 --prepend-https -f {file_path} -d {output_dir}/Screenshots/ --no-prompt"
        
        else:
            if not target.startswith(('http://', 'https://')):
                target_url = f"https://{target}"
            else:
                target_url = target
            
            command = f"eyewitness --web --timeout 30 --threads 500 --prepend-https --single {target_url} -d {output_dir}/Screenshots/ --no-prompt"
        
        info(f"Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            info(f"Screenshots saved to: {output_dir}/Screenshots/")
            return True
        else:
            error(f"Eyewitness failed: {result.stderr}")
            return False
    except Exception as e:
        error(f"Error executing eyewitness: {e}")
        return False
