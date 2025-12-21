# VAJRA/Modules/nmap.py
# Nmap module execution with integrated submenu and auto mode support

import subprocess
import os
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Engine.logger import info, error, success
from Engine.input_utils import get_input, clear_input_buffer
from Engine.report import generate_report

def nmap_submenu(input_func=None):
    """
    Display the Nmap scan technique submenu.
    Accepts an optional input function (input_func) to collect input; if not provided,
    falls back to Engine.input_utils.get_input. Returns the chosen technique and report preference.
    """

    # choose prompt function
    prompt = input_func if input_func is not None else get_input

    nmap_menu = """
    | Nmap Scan Techniques:
    |---|
    [1] Quick Scan (Top 1000 ports) (Default)
    [2] Full Port Scan (1-65535)
    [3] Fast Scan (-A)
    [4] UDP Scan (Top 100 UDP ports)
    """

    print(nmap_menu)

   
    try:
        clear_input_buffer()
    except:
        pass

    while True:
        try:
            choice = prompt("Choose scan type (1-4) [1] > ").strip()

            if not choice:
                scan_type = 'quick'
            elif choice in ['1', '2', '3', '4']:
                techniques = {'1': 'quick', '2': 'full', '3': 'fast', '4': 'udp'}
                scan_type = techniques[choice]
            else:
                error("Invalid choice. Please select 1-4.")
                continue

            report_choice = prompt("Do you want to generate a report? (y/n) > ").strip().lower()
            if not report_choice:
                generate_report_flag = False
            else:
                generate_report_flag = (report_choice == 'y')
            return scan_type, generate_report_flag

        except KeyboardInterrupt:
            return 'quick', False  # Default on interrupt

def _ensure_logs_dir(output_dir):
    """Ensures the Logs subdirectory exists."""
    logs_dir = os.path.join(output_dir, "Logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def run(target, output_dir, runtime_control=None, is_auto_mode=False):
    """Run the nmap tool on the target.
    
    Args:
        target: The target to scan
        output_dir: Directory to save results  
        runtime_control: Runtime control object (optional)
        is_auto_mode: If True, use default settings without prompting (for 'Run All')
    """
    info("--- Starting module: Nmap ---")

    if is_auto_mode:
        info("Auto mode: Using default Quick Scan (Option 1)")
        scan_type = 'quick'
        nmap_report_enabled = False
    else:
        scan_type, nmap_report_enabled = nmap_submenu()

    logs_dir = _ensure_logs_dir(output_dir)

    out_paths = {
        'quick': (os.path.join(logs_dir, "nmap_top1000.txt"), os.path.join(logs_dir, "nmap_top1000.xml")),
        'full': (os.path.join(logs_dir, "nmap_full.txt"), os.path.join(logs_dir, "nmap_full.xml")),
        'fast': (os.path.join(logs_dir, "nmap_fastA.txt"), os.path.join(logs_dir, "nmap_fastA.xml")),
        'udp': (os.path.join(logs_dir, "nmap_udp.txt"), os.path.join(logs_dir, "nmap_udp.xml"))
    }

    commands = {
        'quick': ["nmap", target, "-T4", "--top-ports", "1000", "-sS", "-sV", "-O"],
        'full': ["nmap", target, "-T4", "-p-", "-sS", "-sV", "-O"],
        'fast': ["nmap", target, "-T4", "-A"],
        'udp': ["nmap", target, "-T4", "-sU", "--top-ports", "100"]
    }

    if scan_type not in commands:
        error(f"Invalid scan type: {scan_type}")
        return
    
    command = commands.get(scan_type)
    out_n, out_x = out_paths.get(scan_type)

    command.extend(["-oN", out_n, "-oX", out_x])

    try:
        info(f"Running: {' '.join(command)}")
        
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            info(f"Nmap {scan_type} scan completed.")
            info(f"Output: {out_n}")

            if nmap_report_enabled:
                info("Generating HTML report...")
                # We pass "5" because that's the module choice for Nmap from the main menu
                if generate_report(target, output_dir, "5"):
                    success("HTML report generation successful.")
                else:
                    error("Failed to generate HTML report.")
            else:
                info("Nmap scan completed without report generation.")
        else:
            error(f"Nmap failed with return code {result.returncode}: {result.stderr.strip()}")

    except FileNotFoundError:
        error("Nmap command not found. Please ensure Nmap is installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        error(f"Nmap failed: {e.stderr.strip()}")
    except Exception as e:
        error(f"An error occurred while executing nmap: {e}")

    success("Module Nmap completed successfully.")
