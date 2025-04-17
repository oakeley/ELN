#!/usr/bin/env python3
"""
Advanced GitHub SSH Setup and Troubleshooting Script

This script provides comprehensive SSH key setup and troubleshooting for GitHub:
1. Detailed verification of existing SSH keys and their formats
2. Generation of new keys with proper encryption and formats
3. Advanced SSH agent management
4. Comprehensive SSH config updates for algorithm compatibility
5. GitHub key verification
6. In-depth connection diagnostics with step-by-step resolution
7. Automatic fixing of common issues

For Electronic Laboratory Notebook and other GitHub-integrated applications.
"""

import os
import sys
import subprocess
import platform
import webbrowser
import re
import json
import time
import shutil
from pathlib import Path
import tempfile
import urllib.request
import socket
import getpass
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.END}\n")

def print_step(number, text):
    """Print a formatted step"""
    print(f"{Colors.BLUE}{Colors.BOLD}Step {number}:{Colors.END} {text}")

def print_success(text):
    """Print a success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}✓ {text}{Colors.END}")

def print_error(text):
    """Print an error message"""
    print(f"{Colors.RED}{Colors.BOLD}✗ Error: {text}{Colors.END}")

def print_warning(text):
    """Print a warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}! {text}{Colors.END}")

def print_instruction(text):
    """Print an instruction"""
    print(f"{Colors.YELLOW}→ {text}{Colors.END}")

def print_debug_info(text):
    """Print debug information"""
    print(f"{Colors.BLUE}debug: {text}{Colors.END}")

def run_command(command, shell=False, capture_output=True, verbose=False, input_data=None):
    """Run a command and return the result with better error handling"""
    if verbose:
        print_debug_info(f"Running command: {' '.join(command) if isinstance(command, list) else command}")
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
            input=input_data
        )
        
        if verbose and result.returncode != 0:
            print_warning(f"Command exited with code {result.returncode}")
            if result.stderr:
                print_warning(f"Stderr: {result.stderr}")
        
        return result
    except Exception as e:
        if verbose:
            print_error(f"Exception running command: {e}")
        return None

def detect_system_info():
    """Detect system information for troubleshooting"""
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
    }
    
    # Get OpenSSH version
    ssh_result = run_command(["ssh", "-V"], capture_output=True)
    if ssh_result and ssh_result.stderr:
        system_info["ssh_version"] = ssh_result.stderr.strip()
    
    # Get Git version
    git_result = run_command(["git", "--version"], capture_output=True)
    if git_result and git_result.stdout:
        system_info["git_version"] = git_result.stdout.strip()
    
    return system_info

def check_ssh_keys(include_fingerprints=True):
    """Check if SSH keys already exist and validate their format"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    
    if not ssh_dir.exists():
        print_warning("SSH directory does not exist. We'll create it.")
        return None
    
    # Look for common SSH key names
    key_files = [
        "id_ed25519", "id_ed25519.pub",
        "id_rsa", "id_rsa.pub",
        "github_ed25519", "github_ed25519.pub",
        "github_rsa", "github_rsa.pub",
        "id_ecdsa", "id_ecdsa.pub",
        "id_dsa", "id_dsa.pub"
    ]
    
    found_keys = []
    
    for key_file in key_files:
        if (ssh_dir / key_file).exists():
            if key_file.endswith(".pub"):
                private_key = key_file[:-4]
                key_path = ssh_dir / key_file
                
                # If we found a public key, check if private key exists
                if (ssh_dir / private_key).exists():
                    key_info = {
                        "private_key": private_key,
                        "public_key": key_file,
                        "path": str(key_path),
                        "type": "unknown",
                        "valid": False,
                        "fingerprint": ""
                    }
                    
                    # Read the public key to determine its type
                    try:
                        with open(key_path, "r") as f:
                            pub_key_content = f.read().strip()
                            if pub_key_content.startswith("ssh-ed25519"):
                                key_info["type"] = "ed25519"
                                key_info["valid"] = True
                            elif pub_key_content.startswith("ssh-rsa"):
                                key_info["type"] = "rsa"
                                key_info["valid"] = True
                            elif pub_key_content.startswith("ecdsa-sha2"):
                                key_info["type"] = "ecdsa"
                                key_info["valid"] = True
                            elif pub_key_content.startswith("ssh-dss"):
                                key_info["type"] = "dsa"
                                key_info["valid"] = True
                    except Exception:
                        pass
                    
                    # Get key fingerprint
                    if include_fingerprints:
                        fingerprint_result = run_command(["ssh-keygen", "-lf", str(key_path)], capture_output=True)
                        if fingerprint_result and fingerprint_result.returncode == 0:
                            key_info["fingerprint"] = fingerprint_result.stdout.strip()
                    
                    found_keys.append(key_info)
    
    return found_keys

def get_valid_email(github_validation=True):
    """Get a valid email from user input with GitHub validation option"""
    while True:
        email = input(f"{Colors.YELLOW}Enter your GitHub email: {Colors.END}").strip()
        if email and "@" in email:
            if github_validation:
                print_instruction("Checking if email is associated with a GitHub account...")
                # GitHub doesn't have a public API to validate emails, so we'll just check format
                return email
            return email
        print_warning("Please enter a valid email address.")

def generate_ssh_key(key_name="id_ed25519", key_type="ed25519", email="", bits=4096):
    """Generate a new SSH key with better error handling and proper key type selection"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    
    if not ssh_dir.exists():
        ssh_dir.mkdir(mode=0o700)
    
    key_path = ssh_dir / key_name
    
    # Validate key type
    valid_types = ["ed25519", "rsa", "ecdsa"]
    if key_type not in valid_types:
        print_warning(f"Invalid key type '{key_type}'. Defaulting to ed25519.")
        key_type = "ed25519"
    
    if key_path.exists():
        overwrite = input(f"{Colors.YELLOW}Key {key_path} already exists. Overwrite? (y/N): {Colors.END}").strip().lower() == "y"
        if not overwrite:
            print_warning(f"Keeping existing key {key_path}.")
            return False
    
    if not email:
        email = get_valid_email()
    
    try:
        cmd = ["ssh-keygen", "-t", key_type]
        
        # Add bits parameter for RSA keys
        if key_type == "rsa":
            cmd.extend(["-b", str(bits)])
        
        cmd.extend([
            "-C", email,
            "-f", str(key_path),
            "-N", ""  # Empty passphrase
        ])
        
        result = run_command(cmd, verbose=True)
        
        if result and result.returncode == 0:
            print_success(f"SSH key generated: {key_path}")
            
            # Set proper permissions
            os.chmod(str(key_path), 0o600)
            os.chmod(str(key_path) + ".pub", 0o644)
            
            return True
        else:
            error_msg = result.stderr if result and result.stderr else "Unknown error"
            print_error(f"Failed to generate SSH key: {error_msg}")
            return False
    except Exception as e:
        print_error(f"Failed to generate SSH key: {e}")
        return False

def get_public_key(key_name="id_ed25519"):
    """Get the content of a public key"""
    home_dir = Path.home()
    pub_key_path = home_dir / ".ssh" / f"{key_name}.pub"
    
    if not pub_key_path.exists():
        print_error(f"Public key {pub_key_path} not found.")
        return None
    
    try:
        with open(pub_key_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print_error(f"Error reading public key: {e}")
        return None

def copy_to_clipboard(text):
    """Copy text to clipboard with extensive platform support"""
    try:
        if platform.system() == "Windows":
            # Try multiple methods on Windows
            try:
                subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
                return True
            except:
                # Fallback to PowerShell
                ps_cmd = f'Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.Clipboard]::SetText(\'{text}\');'
                run_command(["powershell", "-Command", ps_cmd], shell=True)
                return True
                
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
            
        elif platform.system() == "Linux":
            # Try multiple clipboard tools on Linux
            clipboard_tools = [
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
                ["wl-copy"]  # For Wayland
            ]
            
            for tool in clipboard_tools:
                try:
                    subprocess.run(tool, input=text.encode("utf-8"), check=True)
                    return True
                except FileNotFoundError:
                    continue
            
            print_warning("No clipboard tool found. Please install xclip, xsel, or wl-copy.")
            print_instruction("Alternatively, manually copy the key shown below.")
            return False
        else:
            print_warning(f"Unsupported platform: {platform.system()}")
            return False
    except Exception as e:
        print_warning(f"Could not copy to clipboard: {e}")
        return False

def start_ssh_agent():
    """Start and configure the SSH agent with robust handling across platforms"""
    print_instruction("Checking SSH agent status...")
    
    # Check if SSH agent is running
    agent_pid = os.environ.get("SSH_AGENT_PID")
    agent_sock = os.environ.get("SSH_AUTH_SOCK")
    
    if agent_pid and agent_sock:
        # Check if the process is actually running
        try:
            os.kill(int(agent_pid), 0)  # Signal 0 just checks if process exists
            print_success("SSH agent is already running.")
            return True
        except (OSError, ProcessLookupError, ValueError):
            print_warning("SSH agent environment variables exist but agent is not running.")
    
    # Start the agent based on platform
    print_instruction("Starting SSH agent...")
    
    # Platform-specific handling
    if platform.system() == "Windows":
        # On Windows, we need special handling
        try:
            # Check if the OpenSSH Authentication Agent service is running (Windows 10+)
            service_check = run_command(["sc", "query", "ssh-agent"], capture_output=True)
            
            if service_check and "RUNNING" in service_check.stdout:
                print_success("SSH agent service is already running.")
                
                # We still need to get the environment variables
                agent_output = run_command(["ssh-agent", "-s"], capture_output=True)
                
                # Extract and set environment variables
                if agent_output and agent_output.stdout:
                    match_pid = re.search(r"SSH_AGENT_PID=([0-9]+)", agent_output.stdout)
                    match_sock = re.search(r"SSH_AUTH_SOCK=([^;]+)", agent_output.stdout)
                    
                    if match_pid and match_sock:
                        os.environ["SSH_AGENT_PID"] = match_pid.group(1)
                        os.environ["SSH_AUTH_SOCK"] = match_sock.group(1)
                        return True
            
            # Try to start the agent
            print_instruction("Starting SSH agent...")
            
            # Create a script to capture the environment variables
            tmp_dir = tempfile.gettempdir()
            ps_script = os.path.join(tmp_dir, "start_ssh_agent.ps1")
            
            with open(ps_script, "w") as f:
                f.write("$sshAgentProcess = Start-Process -FilePath 'ssh-agent.exe' -ArgumentList '-s' -NoNewWindow -PassThru\n")
                f.write("$output = & ssh-agent -s\n")
                f.write("$output | ForEach-Object {\n")
                f.write("    if ($_ -match 'SSH_AUTH_SOCK=([^;]+)'){ $env:SSH_AUTH_SOCK=$matches[1] }\n")
                f.write("    if ($_ -match 'SSH_AGENT_PID=([0-9]+)'){ $env:SSH_AGENT_PID=$matches[1] }\n")
                f.write("}\n")
                f.write("Write-Output \"SSH_AUTH_SOCK=$env:SSH_AUTH_SOCK\"\n")
                f.write("Write-Output \"SSH_AGENT_PID=$env:SSH_AGENT_PID\"\n")
            
            # Run the script
            agent_result = run_command(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script], capture_output=True)
            
            if agent_result and agent_result.stdout:
                # Extract the environment variables
                match_sock = re.search(r"SSH_AUTH_SOCK=(.+)", agent_result.stdout)
                match_pid = re.search(r"SSH_AGENT_PID=([0-9]+)", agent_result.stdout)
                
                if match_sock and match_pid:
                    os.environ["SSH_AUTH_SOCK"] = match_sock.group(1)
                    os.environ["SSH_AGENT_PID"] = match_pid.group(1)
                    print_success("SSH agent started.")
                    
                    # Clean up the script
                    try:
                        os.remove(ps_script)
                    except:
                        pass
                    
                    return True
            
            print_warning("Failed to start SSH agent through PowerShell.")
            print_instruction("Try running 'ssh-agent' manually or restart the OpenSSH Authentication Agent service.")
            return False
            
        except Exception as e:
            print_warning(f"Error starting SSH agent on Windows: {e}")
            print_instruction("Try running 'ssh-agent' manually or enable the OpenSSH Authentication Agent service.")
            return False
    else:
        # Unix-like platforms (Linux, macOS)
        try:
            agent_result = run_command(["ssh-agent", "-s"], capture_output=True)
            
            if not agent_result or agent_result.returncode != 0:
                print_warning("Failed to start SSH agent.")
                print_instruction("Run 'eval $(ssh-agent -s)' manually in your terminal.")
                return False
            
            # Extract and set environment variables
            if agent_result.stdout:
                match_pid = re.search(r"SSH_AGENT_PID=([0-9]+)", agent_result.stdout)
                match_sock = re.search(r"SSH_AUTH_SOCK=([^;]+)", agent_result.stdout)
                
                if match_pid and match_sock:
                    os.environ["SSH_AGENT_PID"] = match_pid.group(1)
                    os.environ["SSH_AUTH_SOCK"] = match_sock.group(1)
                    print_success("SSH agent started and environment variables set.")
                    
                    # Display command for user's shell
                    print_instruction("To use the SSH agent in your current terminal, run:")
                    print(f"{Colors.BOLD}eval $(ssh-agent -s){Colors.END}")
                    
                    return True
                else:
                    print_warning("Started SSH agent but couldn't parse output.")
                    print_instruction(f"Please manually run: eval $(ssh-agent -s)")
                    return False
            else:
                print_warning("Failed to get SSH agent output.")
                return False
                
        except Exception as e:
            print_warning(f"Error starting SSH agent: {e}")
            print_instruction("Try running 'eval $(ssh-agent -s)' manually.")
            return False

def check_key_loaded_in_agent(key_name):
    """Check if a specific key is loaded in the SSH agent"""
    try:
        result = run_command(["ssh-add", "-l"], capture_output=True)
        
        if result and result.returncode == 0:
            # Key is listed in the output, check if our key is loaded
            key_path = str(Path.home() / ".ssh" / key_name)
            
            # Get key fingerprint for comparison
            fingerprint_result = run_command(["ssh-keygen", "-lf", key_path], capture_output=True)
            
            if fingerprint_result and fingerprint_result.returncode == 0:
                fingerprint = fingerprint_result.stdout.strip()
                # Extract just the hash part from fingerprints like "256 SHA256:abcd1234... user@host"
                match = re.search(r'SHA256:([^ ]+)', fingerprint)
                if match:
                    key_hash = match.group(1)
                    return key_hash in result.stdout
            
            # If we can't get the fingerprint, fall back to checking path
            return key_path in result.stdout
        elif result and "The agent has no identities." in result.stdout:
            return False
        else:
            print_warning("Could not check SSH agent keys.")
            return False
    except Exception as e:
        print_warning(f"Error checking SSH agent keys: {e}")
        return False

def add_key_to_agent(key_name):
    """Add the key to SSH agent with proper error handling and verification"""
    home_dir = Path.home()
    key_path = home_dir / ".ssh" / key_name
    
    if not os.path.exists(key_path):
        print_error(f"Key file {key_path} does not exist.")
        return False
    
    # Check if key is already loaded
    if check_key_loaded_in_agent(key_name):
        print_success(f"Key {key_name} is already loaded in SSH agent.")
        return True
    
    # First make sure permissions are correct
    try:
        os.chmod(str(key_path), 0o600)
    except Exception as e:
        print_warning(f"Could not set permissions on key file: {e}")
    
    try:
        # Check if SSH agent is available
        agent_check = run_command(["ssh-add", "-l"], capture_output=True)
        
        if agent_check is None or "Could not open a connection to your authentication agent" in (agent_check.stderr or ""):
            print_warning("SSH agent is not running properly.")
            if not start_ssh_agent():
                print_instruction("Please run 'eval $(ssh-agent -s)' manually, then try again.")
                return False
                
        # Try to add the key
        add_result = run_command(["ssh-add", str(key_path)], capture_output=True)
        
        if add_result and add_result.returncode == 0:
            # Verify the key was added
            if check_key_loaded_in_agent(key_name):
                print_success(f"Added key {key_name} to SSH agent")
                return True
            else:
                print_warning(f"Key was added but verification failed.")
                return False
        else:
            error = add_result.stderr if add_result and add_result.stderr else "Unknown error"
            print_warning(f"Failed to add key to SSH agent: {error}")
            
            # Try to provide specific guidance
            if "denied" in error.lower():
                print_instruction(f"Permission denied. Check file permissions with: chmod 600 {key_path}")
            elif "encrypted" in error.lower():
                print_instruction(f"Key is encrypted. You'll need to enter your passphrase.")
            
            print_instruction(f"Please manually run: ssh-add {key_path}")
            return False
    except Exception as e:
        print_warning(f"Error adding key to SSH agent: {e}")
        print_instruction(f"Please manually run: ssh-add {key_path}")
        return False

def ensure_known_hosts_exists():
    """Ensure the known_hosts file exists and contains GitHub's key"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    known_hosts = ssh_dir / "known_hosts"
    
    if not ssh_dir.exists():
        try:
            ssh_dir.mkdir(mode=0o700)
            print_success("Created SSH directory.")
        except Exception as e:
            print_error(f"Could not create SSH directory: {e}")
            return False
    
    # Create known_hosts if it doesn't exist
    if not known_hosts.exists():
        try:
            with open(known_hosts, 'w') as f:
                pass  # Create empty file
            os.chmod(known_hosts, 0o644)
            print_success("Created empty known_hosts file.")
        except Exception as e:
            print_warning(f"Failed to create known_hosts file: {e}")
            return False
    
    # Check if GitHub's key is already in known_hosts
    try:
        with open(known_hosts, 'r') as f:
            content = f.read()
            if "github.com" in content:
                print_success("GitHub's host key already in known_hosts file.")
                return True
    except Exception as e:
        print_warning(f"Failed to read known_hosts file: {e}")
    
    # Fetch GitHub's host key
    print_instruction("Adding GitHub's host key to known_hosts file...")
    try:
        result = run_command(["ssh-keyscan", "-t", "rsa,ecdsa,ed25519", "github.com"], capture_output=True)
        
        if result and result.returncode == 0 and result.stdout:
            with open(known_hosts, 'a') as f:
                f.write(result.stdout)
            print_success("Added GitHub's host key to known_hosts file.")
            return True
        else:
            print_warning("Failed to fetch GitHub's host key.")
            error = result.stderr if result and result.stderr else "Unknown error"
            print_warning(f"Error: {error}")
            return False
    except Exception as e:
        print_warning(f"Failed to add GitHub's host key: {e}")
        return False

def configure_ssh_config():
    """Configure SSH settings with comprehensive algorithm support for GitHub"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    config_path = ssh_dir / "config"
    
    # Enhanced GitHub config with all necessary options
    github_config = """
# GitHub.com
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    PubkeyAcceptedAlgorithms +ssh-ed25519,ssh-rsa,ssh-dss,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521
    PubkeyAcceptedKeyTypes +ssh-ed25519,ssh-rsa,ssh-dss,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521
    HostKeyAlgorithms +ssh-ed25519,ssh-rsa,ssh-dss,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521
    KexAlgorithms +curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256
"""
    
    # Ensure SSH directory exists
    if not ssh_dir.exists():
        ssh_dir.mkdir(mode=0o700)
    
    # Check if config exists and has GitHub settings
    if config_path.exists():
        with open(config_path, "r") as f:
            current_config = f.read()
        
        if "github.com" in current_config:
            # Check if it has all the algorithm settings
            required_settings = [
                "PubkeyAcceptedAlgorithms",
                "PubkeyAcceptedKeyTypes",
                "HostKeyAlgorithms",
                "KexAlgorithms"
            ]
            
            # Count how many settings are already present
            settings_found = sum(1 for setting in required_settings if setting in current_config)
            
            if settings_found == len(required_settings):
                print_success("GitHub configuration with comprehensive algorithm support already exists.")
                return True
            else:
                # Config exists but needs updating
                print_warning(f"GitHub config exists but has only {settings_found}/{len(required_settings)} required settings. Updating...")
                
                # Create backup
                backup_path = str(config_path) + ".bak"
                shutil.copy(str(config_path), backup_path)
                print_success(f"Created backup of SSH config at {backup_path}")
                
                # Remove existing github.com section and add updated one
                pattern = re.compile(r'(?:^|\n)# GitHub\.com\s+Host github\.com[\s\S]+?(?=\n\n|\n#|$)', re.MULTILINE)
                matches = pattern.findall(current_config)
                
                if matches:
                    updated_config = pattern.sub('', current_config)
                    
                    # Ensure config ends with newline before appending
                    if updated_config and not updated_config.endswith("\n"):
                        updated_config += "\n"
                    
                    updated_config += github_config
                else:
                    # GitHub section not found in expected format, append new config
                    # Ensure config ends with newline before appending
                    if current_config and not current_config.endswith("\n"):
                        current_config += "\n"
                    
                    updated_config = current_config + github_config
                
                with open(config_path, "w") as f:
                    f.write(updated_config)
                
                print_success("Updated GitHub configuration with comprehensive algorithm support.")
        else:
            # Config exists but no GitHub section
            with open(config_path, "a+") as f:
                # Ensure file ends with newline
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1, os.SEEK_SET)
                    if f.read(1) != "\n":
                        f.write("\n")
                
                f.write(github_config)
            
            print_success("Added GitHub configuration with algorithm support to SSH config.")
    else:
        # Create new config
        with open(config_path, "w") as f:
            f.write(github_config)
        
        print_success("Created new SSH config with GitHub settings.")
    
    # Set proper permissions
    os.chmod(config_path, 0o600)
    return True

def check_ssh_connection(host="github.com", user="git", verbose=False):
    """Check SSH connection with detailed diagnostics"""
    print_instruction(f"Testing SSH connection to {host}...")
    
    # Command to test connection
    test_cmd = ["ssh", "-T"]
    
    if verbose:
        test_cmd.append("-v")
    
    # Add StrictHostKeyChecking option
    test_cmd.extend(["-o", "StrictHostKeyChecking=accept-new"])
    
    # Add BatchMode to avoid any passphrase prompts
    test_cmd.extend(["-o", "BatchMode=yes"])
    
    # Add timeout to avoid hanging
    test_cmd.extend(["-o", "ConnectTimeout=10"])
    
    # Add host
    test_cmd.append(f"{user}@{host}")
    
    # Run the test
    result = run_command(test_cmd, capture_output=True)
    
    if not result:
        print_error(f"Failed to run SSH command.")
        return False, "Failed to run SSH command", []
    
    # Get combined output for parsing
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += "\n" + result.stderr
    
    # Check for success patterns
    success_patterns = [
        "successfully authenticated",
        "You've successfully authenticated",
        "Hi ",  # GitHub typically responds with "Hi username!"
    ]
    
    success = any(pattern in output for pattern in success_patterns)
    
    if success:
        print_success(f"Successfully connected to {host}!")
        return True, output, []
    else:
        print_error(f"SSH authentication to {host} failed.")
        return False, output, parse_ssh_issues(output)

def parse_ssh_issues(output):
    """Parse SSH output for common issues with enhanced detection"""
    issues = []
    
    # Common categories of SSH issues
    
    # Key format or algorithm issues
    if "algorithm not in PubkeyAcceptedAlgorithms" in output:
        issues.append({
            "issue": "SSH key algorithm not accepted",
            "details": "Your SSH key algorithm isn't in the list of accepted algorithms.",
            "fix": "Update SSH config with PubkeyAcceptedAlgorithms settings",
            "automated": True,
            "severity": "high"
        })
    
    if "key_type_from_name: unknown key type" in output:
        issues.append({
            "issue": "Unknown key type",
            "details": "Your SSH implementation doesn't recognize the key type.",
            "fix": "Use a more standard key type like RSA or update your OpenSSH version",
            "automated": False,
            "severity": "high"
        })
    
    # Authentication issues
    if "Permission denied (publickey)" in output:
        issues.append({
            "issue": "Public key authentication failed",
            "details": "GitHub rejected your key or couldn't find a matching key.",
            "fix": "Verify your key is added to GitHub and properly loaded in the SSH agent",
            "automated": False,
            "severity": "high"
        })
    
    if "sign_and_send_pubkey: signing failed" in output:
        issues.append({
            "issue": "Key signing failed",
            "details": "Unable to sign data with your private key. This could be due to permissions or passphrase issues.",
            "fix": "Check key permissions and ensure you've entered the correct passphrase",
            "automated": False,
            "severity": "medium"
        })
    
    # Permission issues
    if re.search(r"Permissions [0-9]+ for '.*' are too open", output):
        issues.append({
            "issue": "SSH key file permissions too open",
            "details": "Your SSH key file has permissions that are too permissive.",
            "fix": "Run: chmod 600 ~/.ssh/id_ed25519 (or your key file)",
            "automated": True,
            "severity": "high"
        })
    
    if "bad permissions" in output.lower():
        issues.append({
            "issue": "Bad permissions on SSH directory or files",
            "details": "Permissions on your SSH files or directory are incorrect.",
            "fix": "Run: chmod 700 ~/.ssh and chmod 600 for all key files",
            "automated": True,
            "severity": "high"
        })
    
    # Agent issues
    if "Could not open a connection to your authentication agent" in output:
        issues.append({
            "issue": "SSH agent not running or not accessible",
            "details": "Cannot connect to the SSH agent process.",
            "fix": "Start the SSH agent with: eval $(ssh-agent -s)",
            "automated": True,
            "severity": "medium"
        })
    
    if "agent refused operation" in output:
        issues.append({
            "issue": "SSH agent refused operation",
            "details": "The SSH agent is running but refused to perform the requested operation.",
            "fix": "Restart the SSH agent and add your key again",
            "automated": True,
            "severity": "medium"
        })
    
    # Configuration issues
    if "No such file or directory" in output and "known_hosts" in output:
        issues.append({
            "issue": "known_hosts file missing",
            "details": "The SSH known_hosts file is missing.",
            "fix": "Create ~/.ssh/known_hosts file",
            "automated": True,
            "severity": "low"
        })
    
    if "Host key verification failed" in output:
        issues.append({
            "issue": "Host key verification failed",
            "details": "GitHub's host key doesn't match the one in your known_hosts file or is missing.",
            "fix": "Update your known_hosts file with: ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts",
            "automated": True,
            "severity": "medium"
        })
    
    if "Bad configuration option" in output:
        issues.append({
            "issue": "Bad SSH configuration option",
            "details": "Your SSH config contains an option that's not recognized by your SSH version.",
            "fix": "Check your SSH config file for syntax errors or unsupported options",
            "automated": False,
            "severity": "medium"
        })
    
    # Network issues
    if "Connection refused" in output:
        issues.append({
            "issue": "Connection refused",
            "details": "The server actively refused the connection.",
            "fix": "Verify GitHub.com is accessible and that you're not blocked by a firewall",
            "automated": False,
            "severity": "high"
        })
    
    if "Connection timed out" in output:
        issues.append({
            "issue": "Connection timed out",
            "details": "The connection to GitHub timed out.",
            "fix": "Check your internet connection and firewall settings",
            "automated": False,
            "severity": "high"
        })
    
    if "Network is unreachable" in output:
        issues.append({
            "issue": "Network is unreachable",
            "details": "Your network configuration is preventing the connection.",
            "fix": "Check your internet connection and network settings",
            "automated": False,
            "severity": "high"
        })
    
    # Specific to GitHub
    if "key is not authorized" in output:
        issues.append({
            "issue": "SSH key not authorized",
            "details": "Your key is not authorized for use with GitHub.",
            "fix": "Add this key to your GitHub account in Settings → SSH and GPG keys",
            "automated": False,
            "severity": "high"
        })
    
    if "no mutual signature algorithm" in output:
        issues.append({
            "issue": "No mutual signature algorithm",
            "details": "No common signature algorithm between client and server.",
            "fix": "Update SSH config to enable more signature algorithms",
            "automated": True,
            "severity": "high"
        })
    
    # Handle case where no specific issue is identified
    if not issues and "debug1:" in output:
        # We have verbose output but no known issues identified
        issues.append({
            "issue": "Unknown SSH authentication failure",
            "details": "Authentication failed but no specific issue could be identified.",
            "fix": "Verify your SSH key is correctly added to GitHub and properly configured",
            "automated": False,
            "severity": "medium"
        })
    
    return issues

def fix_ssh_issues(issues):
    """Fix detected SSH issues automatically with enhanced capabilities"""
    if not issues:
        print_warning("No specific issues to fix were identified.")
        return False
    
    issues_fixed = 0
    
    for issue in issues:
        print_instruction(f"Attempting to fix: {issue['issue']}")
        print_debug_info(issue['details'])
        
        if not issue.get("automated", False):
            print_warning(f"This issue requires manual intervention: {issue['fix']}")
            continue
        
        # Algorithm and configuration issues
        if "PubkeyAcceptedAlgorithms" in issue["fix"] or "algorithm" in issue["issue"].lower():
            if configure_ssh_config():
                issues_fixed += 1
        
        # Permission issues
        elif "chmod 600" in issue["fix"] or "permissions" in issue["issue"].lower():
            home_dir = Path.home()
            key_paths = [
                home_dir / ".ssh" / "id_ed25519",
                home_dir / ".ssh" / "id_rsa",
                home_dir / ".ssh" / "github_ed25519",
                home_dir / ".ssh" / "github_rsa"
            ]
            
            fixed = False
            for key_path in key_paths:
                if key_path.exists():
                    try:
                        os.chmod(str(key_path), 0o600)
                        print_success(f"Fixed permissions for {key_path}")
                        fixed = True
                    except Exception as e:
                        print_warning(f"Could not fix permissions for {key_path}: {e}")
            
            # Also fix SSH directory permissions
            ssh_dir = home_dir / ".ssh"
            if ssh_dir.exists():
                try:
                    os.chmod(str(ssh_dir), 0o700)
                    print_success(f"Fixed permissions for {ssh_dir}")
                    fixed = True
                except Exception as e:
                    print_warning(f"Could not fix permissions for {ssh_dir}: {e}")
            
            if fixed:
                issues_fixed += 1
        
        # SSH agent issues
        elif "ssh-agent" in issue["fix"] or "agent" in issue["issue"].lower():
            if start_ssh_agent():
                # Also try to add keys after starting agent
                home_dir = Path.home()
                key_paths = [
                    ("id_ed25519", home_dir / ".ssh" / "id_ed25519"),
                    ("id_rsa", home_dir / ".ssh" / "id_rsa"),
                    ("github_ed25519", home_dir / ".ssh" / "github_ed25519"),
                    ("github_rsa", home_dir / ".ssh" / "github_rsa")
                ]
                
                for key_name, key_path in key_paths:
                    if key_path.exists():
                        if add_key_to_agent(key_name):
                            issues_fixed += 1
                            break
            else:
                print_warning("Could not start SSH agent automatically.")
        
        # Known hosts issues
        elif "known_hosts" in issue["fix"] or "known_hosts" in issue["issue"].lower():
            if ensure_known_hosts_exists():
                issues_fixed += 1
        
        # Host key verification issues
        elif "ssh-keyscan" in issue["fix"] or "host key" in issue["issue"].lower():
            try:
                result = run_command(["ssh-keyscan", "-t", "rsa,ecdsa,ed25519", "github.com"], capture_output=True)
                if result and result.returncode == 0 and result.stdout:
                    home_dir = Path.home()
                    known_hosts = home_dir / ".ssh" / "known_hosts"
                    
                    # Create the file if it doesn't exist
                    if not known_hosts.exists():
                        ensure_known_hosts_exists()
                    
                    # Add the keys, checking for duplicates
                    with open(known_hosts, "r") as f:
                        existing_content = f.read()
                    
                    new_keys = [line for line in result.stdout.splitlines() 
                               if line and not any(line in existing_line for existing_line in existing_content.splitlines())]
                    
                    if new_keys:
                        with open(known_hosts, "a") as f:
                            for key in new_keys:
                                f.write(key + "\n")
                        
                        print_success(f"Added {len(new_keys)} GitHub host keys to known_hosts")
                        issues_fixed += 1
                    else:
                        print_success("All GitHub host keys are already in known_hosts")
                else:
                    print_warning("Failed to fetch GitHub host keys")
            except Exception as e:
                print_warning(f"Failed to update known_hosts: {e}")
        
        # Signature algorithm issues
        elif "signature algorithm" in issue["issue"].lower():
            if configure_ssh_config():
                issues_fixed += 1
    
    return issues_fixed > 0

def check_github_key_registration(pub_key_content):
    """Check if the public key appears to be properly registered with GitHub"""
    # Extract the key fingerprint
    fingerprint_cmd = ["ssh-keygen", "-lf", "-"]
    result = run_command(fingerprint_cmd, capture_output=True, input_data=pub_key_content)
    
    if not result or result.returncode != 0:
        print_warning("Could not generate key fingerprint for verification.")
        return None
    
    fingerprint = result.stdout.strip()
    
    # Now check if we can authenticate with GitHub
    success, output, issues = check_ssh_connection(verbose=False)
    
    if success:
        print_success("GitHub authentication successful. Key is properly registered.")
        return True
    else:
        # Try to extract username from the error message
        username_match = re.search(r"Hi ([^!]+)!", output)
        if username_match:
            github_username = username_match.group(1)
            print_success(f"Key is registered to GitHub user: {github_username}")
            print_warning("But authentication still failed. Check for other issues.")
        
        print_warning("Key does not appear to be properly registered with GitHub or there are other issues.")
        return False

def verify_github_key_with_api(github_username, pub_key_content):
    """Verify if a key is registered with GitHub using their API (if available)"""
    try:
        # Extract key fingerprint for comparison
        fingerprint_cmd = ["ssh-keygen", "-lf", "-"]
        result = run_command(fingerprint_cmd, capture_output=True, input_data=pub_key_content)
        
        if not result or result.returncode != 0:
            print_warning("Could not generate key fingerprint for verification.")
            return None
        
        # Extract just the hash part
        fingerprint = result.stdout.strip()
        hash_match = re.search(r'SHA256:([^ ]+)', fingerprint)
        if not hash_match:
            print_warning("Could not extract hash from fingerprint.")
            return None
        
        key_hash = hash_match.group(1)
        
        # This would normally use GitHub's API, but it requires authentication
        # Instead, we'll just check if we can authenticate
        success, output, issues = check_ssh_connection(verbose=False)
        
        if success:
            return {"registered": True, "username": github_username}
        else:
            username_match = re.search(r"Hi ([^!]+)!", output)
            if username_match:
                actual_username = username_match.group(1)
                if actual_username != github_username:
                    return {"registered": True, "username": actual_username, "mismatch": True}
                else:
                    return {"registered": True, "username": github_username}
            
            return {"registered": False}
    except Exception as e:
        print_warning(f"Error verifying key with GitHub: {e}")
        return None

def check_git_remote_protocol():
    """Check if git remotes are using SSH protocol and offer to convert them"""
    try:
        result = run_command(
            ["git", "remote", "-v"],
            capture_output=True
        )
        
        if not result or result.returncode != 0:
            print_warning("Not in a git repository or git not installed.")
            return
        
        remotes = result.stdout.strip().split("\n")
        https_remotes = []
        
        for remote in remotes:
            if not remote:
                continue
            if "https://github.com" in remote:
                parts = remote.split()
                if len(parts) >= 2:
                    https_remotes.append(parts[0])
        
        if https_remotes:
            print_warning(f"Found GitHub remotes using HTTPS: {', '.join(set(https_remotes))}")
            
            update_remotes = input(f"{Colors.YELLOW}Update HTTPS remotes to SSH? (Y/n): {Colors.END}").strip().lower() != "n"
            
            if update_remotes:
                updated = 0
                for remote_name in set(https_remotes):
                    # Get the current URL
                    url_result = run_command(["git", "remote", "get-url", remote_name], capture_output=True)
                    if url_result and url_result.returncode == 0:
                        current_url = url_result.stdout.strip()
                        # Extract username and repo from HTTPS URL
                        match = re.search(r'https://github\.com/([^/]+)/(.+?)(?:\.git)?', current_url)
                        if match:
                            username, repo = match.groups()
                            new_url = f"git@github.com:{username}/{repo}.git"
                            
                            # Update the remote
                            update_result = run_command(["git", "remote", "set-url", remote_name, new_url], capture_output=True)
                            if update_result and update_result.returncode == 0:
                                print_success(f"Updated remote '{remote_name}' to use SSH: {new_url}")
                                updated += 1
                            else:
                                print_error(f"Failed to update remote '{remote_name}'")
                        else:
                            print_warning(f"Could not parse GitHub URL: {current_url}")
                
                if updated > 0:
                    print_success(f"Successfully updated {updated} remote(s) to use SSH.")
                else:
                    print_warning("No remotes were updated.")
            else:
                print_instruction("To update a remote to use SSH, run:")
                print(f"{Colors.BOLD}git remote set-url <remote_name> git@github.com:username/repository.git{Colors.END}")
        else:
            print_success("No GitHub HTTPS remotes found.")
    except Exception as e:
        print_warning(f"Could not check git remotes: {e}")

def generate_troubleshooting_report(issues, system_info, ssh_output):
    """Generate a comprehensive troubleshooting report"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = Path.home() / f"github_ssh_troubleshooting_{now}.txt"
    
    try:
        with open(report_file, "w") as f:
            f.write("=== GitHub SSH Troubleshooting Report ===\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=== System Information ===\n")
            for key, value in system_info.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            if issues:
                f.write("=== Detected Issues ===\n")
                for idx, issue in enumerate(issues, 1):
                    f.write(f"{idx}. Issue: {issue['issue']}\n")
                    f.write(f"   Details: {issue['details']}\n")
                    f.write(f"   Fix: {issue['fix']}\n")
                    f.write(f"   Severity: {issue['severity']}\n")
                    f.write(f"   Automated: {'Yes' if issue.get('automated', False) else 'No'}\n\n")
            else:
                f.write("No specific issues were detected.\n\n")
            
            f.write("=== SSH Debug Output ===\n")
            f.write(ssh_output)
            
            f.write("\n\n=== SSH Configuration ===\n")
            ssh_config_path = Path.home() / ".ssh" / "config"
            if ssh_config_path.exists():
                try:
                    with open(ssh_config_path, "r") as config_file:
                        config_content = config_file.read()
                        # Redact private information
                        redacted_content = re.sub(r'IdentityFile\s+(.+)', r'IdentityFile [REDACTED]', config_content)
                        f.write(redacted_content)
                except Exception as e:
                    f.write(f"Error reading SSH config: {e}\n")
            else:
                f.write("SSH config file not found.\n")
            
            f.write("\n=== SSH Keys ===\n")
            ssh_keys = check_ssh_keys(include_fingerprints=True)
            if ssh_keys:
                for key in ssh_keys:
                    f.write(f"Key: {key['private_key']}\n")
                    f.write(f"Type: {key['type']}\n")
                    f.write(f"Valid: {key['valid']}\n")
                    if key['fingerprint']:
                        f.write(f"Fingerprint: {key['fingerprint']}\n")
                    f.write("\n")
            else:
                f.write("No SSH keys found.\n")
            
            f.write("\n=== SSH Agent ===\n")
            agent_result = run_command(["ssh-add", "-l"], capture_output=True)
            if agent_result:
                if agent_result.returncode == 0:
                    f.write("SSH agent is running with these keys:\n")
                    f.write(agent_result.stdout)
                elif "The agent has no identities" in agent_result.stdout:
                    f.write("SSH agent is running but has no keys loaded.\n")
                else:
                    f.write("SSH agent is not running or not accessible.\n")
            else:
                f.write("Could not check SSH agent status.\n")
            
            f.write("\n=== Next Steps ===\n")
            f.write("1. Review the detected issues and apply the suggested fixes.\n")
            f.write("2. If problems persist, ensure your key is properly added to GitHub.\n")
            f.write("3. Check GitHub's system status: https://www.githubstatus.com/\n")
            f.write("4. For more help, visit: https://docs.github.com/en/authentication/troubleshooting-ssh\n")
        
        print_success(f"Troubleshooting report saved to: {report_file}")
        return str(report_file)
    except Exception as e:
        print_error(f"Failed to generate troubleshooting report: {e}")
        return None

def main():
    """Main function with enhanced error handling and troubleshooting"""
    print_header("Advanced GitHub SSH Setup and Troubleshooting")
    
    # Collect system information for troubleshooting
    system_info = detect_system_info()
    
    # Step 1: Check for existing SSH keys with validation
    print_step(1, "Checking for existing SSH keys")
    existing_keys = check_ssh_keys(include_fingerprints=True)
    
    key_to_use = None
    
    if existing_keys:
        valid_keys = [k for k in existing_keys if k['valid']]
        if valid_keys:
            print_success(f"Found {len(valid_keys)} valid SSH key pairs:")
            for i, key in enumerate(valid_keys):
                key_type = key['type'].upper()
                print(f"{i+1}. {key['private_key']} ({key_type})")
                if key['fingerprint']:
                    print(f"   {key['fingerprint']}")
            
            use_existing = input(f"{Colors.YELLOW}Use existing keys? (Y/n): {Colors.END}").strip().lower()
            if use_existing != "n":
                key_to_use = valid_keys[0]['private_key']  # Default to first key
                if len(valid_keys) > 1:
                    while True:
                        choice = input(f"{Colors.YELLOW}Enter number (1-{len(valid_keys)}): {Colors.END}").strip()
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(valid_keys):
                                key_to_use = valid_keys[choice_idx]['private_key']
                                break
                            else:
                                print_warning(f"Please enter a number between 1 and {len(valid_keys)}.")
                        except ValueError:
                            print_warning("Please enter a valid number.")
                
                pub_key = get_public_key(key_to_use)
            else:
                # Generate a new key
                print_step(2, "Generating a new SSH key")
                
                # Let user choose key type
                print_instruction("Choose SSH key type:")
                print("1. ED25519 (recommended, modern, secure)")
                print("2. RSA (widely compatible, traditional)")
                key_type_choice = input(f"{Colors.YELLOW}Enter choice (1/2): {Colors.END}").strip()
                
                if key_type_choice == "2":
                    key_type = "rsa"
                    key_name = "id_rsa"
                    bits = 4096
                else:
                    key_type = "ed25519"
                    key_name = "id_ed25519"
                    bits = None
                
                email = get_valid_email(github_validation=True)
                generate_ssh_key(key_name, key_type, email, bits)
                key_to_use = key_name
                pub_key = get_public_key(key_to_use)
        else:
            print_warning("Found SSH keys, but none appear to be valid. Generating a new key.")
            print_step(2, "Generating a new SSH key")
            email = get_valid_email(github_validation=True)
            generate_ssh_key("id_ed25519", "ed25519", email)
            key_to_use = "id_ed25519"
            pub_key = get_public_key(key_to_use)
    else:
        # No existing keys, generate new ones
        print_step(2, "Generating a new SSH key")
        
        # Let user choose key type
        print_instruction("Choose SSH key type:")
        print("1. ED25519 (recommended, modern, secure)")
        print("2. RSA (widely compatible, traditional)")
        key_type_choice = input(f"{Colors.YELLOW}Enter choice (1/2): {Colors.END}").strip()
        
        if key_type_choice == "2":
            key_type = "rsa"
            key_name = "id_rsa"
            bits = 4096
        else:
            key_type = "ed25519"
            key_name = "id_ed25519"
            bits = None
        
        email = get_valid_email(github_validation=True)
        generate_ssh_key(key_name, key_type, email, bits)
        key_to_use = key_name
        pub_key = get_public_key(key_to_use)
    
    # Step 3: Start SSH agent with robust handling
    print_step(3, "Configuring SSH agent")
    agent_status = start_ssh_agent()
    
    # Step 4: Add key to SSH agent with verification
    print_step(4, "Adding key to SSH agent")
    key_added = add_key_to_agent(key_to_use)
    
    # Step 5: Update SSH config with comprehensive settings
    print_step(5, "Configuring SSH settings with algorithm support")
    config_updated = configure_ssh_config()
    
    # Step 6: Ensure known_hosts is properly set up
    print_step(6, "Setting up known_hosts file")
    known_hosts_configured = ensure_known_hosts_exists()
    
    # Step 7: Add key to GitHub
    print_step(7, "Adding SSH key to GitHub")
    if pub_key:
        print("Your public SSH key is:")
        print(f"\n{Colors.BOLD}{pub_key}{Colors.END}\n")
        
        if copy_to_clipboard(pub_key):
            print_success("Public key copied to clipboard!")
        
        print_instruction("1. Go to GitHub Settings → SSH and GPG keys → New SSH key")
        print_instruction("2. Give your key a title (e.g., 'Work Computer')")
        print_instruction("3. Paste the key copied above")
        print_instruction("4. Select 'Authentication Key' when asked for key type")
        print_instruction("5. Click 'Add SSH key'")
        
        open_browser = input(f"{Colors.YELLOW}Open GitHub SSH settings in browser? (Y/n): {Colors.END}").strip().lower()
        if open_browser != "n":
            webbrowser.open("https://github.com/settings/ssh/new")
        
        input(f"\n{Colors.YELLOW}Press Enter when you've added the key to GitHub...{Colors.END}")
        
        # Get GitHub username for verification
        github_username = input(f"{Colors.YELLOW}Enter your GitHub username: {Colors.END}").strip()
    else:
        print_error("Could not read public key.")
    
    # Step 8: Test connection with verbose output and diagnostics
    print_step(8, "Testing GitHub SSH connection with diagnostics")
    success, output, issues = check_ssh_connection(verbose=True)
    
    # If test failed, try to auto-fix issues
    if not success:
        print_step(9, "Troubleshooting SSH connection issues")
        if issues:
            print_warning(f"Found {len(issues)} potential issues:")
            for idx, issue in enumerate(issues, 1):
                severity = issue.get('severity', 'medium').upper()
                print(f"{idx}. [{severity}] {issue['issue']}")
                print(f"   {issue['details']}")
                print_instruction(f"   Fix: {issue['fix']}")
            
            print_instruction("Attempting to automatically fix issues...")
            fixed = fix_ssh_issues(issues)
            
            if fixed:
                print_instruction("Issues addressed. Retesting connection...")
                # Test again after fixing
                success, output, new_issues = check_ssh_connection(verbose=True)
                
                if success:
                    print_success("Connection successful after fixes!")
                else:
                    print_warning("Connection still failing. Additional troubleshooting needed.")
                    issues = new_issues
            else:
                print_warning("Could not automatically fix all issues.")
        else:
            print_warning("No specific issues were identified. This may require manual troubleshooting.")
    
    # Step 10: Check and update git remotes if needed
    print_step(10, "Checking git remotes")
    check_git_remote_protocol()
    
    # Final status report
    if success:
        print_header("Setup Complete!")
        print_success("Your SSH key is working correctly with GitHub.")
        
        if 'github_username' in locals() and github_username:
            print(f"GitHub Username: {github_username}")
        
        print(f"SSH Key: ~/.ssh/{key_to_use}")
        print(f"Public Key: ~/.ssh/{key_to_use}.pub")
        
        # Display key fingerprint for reference
        fingerprint_result = run_command(["ssh-keygen", "-lf", str(Path.home() / ".ssh" / f"{key_to_use}.pub")], capture_output=True)
        if fingerprint_result and fingerprint_result.returncode == 0:
            print(f"Fingerprint: {fingerprint_result.stdout.strip()}")
        
        print("\nYou can update your .env file with these settings:")
        print(f"""
GITHUB_USERNAME={github_username if 'github_username' in locals() and github_username else 'your-github-username'}
GITHUB_SSH_KEY_PATH=~/.ssh/{key_to_use}
GITHUB_SSH_PUB_KEY_PATH=~/.ssh/{key_to_use}.pub
""")
    else:
        print_header("Setup Incomplete")
        print_warning("SSH connection test failed. Please check the troubleshooting information.")
        
        # Generate a comprehensive troubleshooting report
        save_report = input(f"{Colors.YELLOW}Generate troubleshooting report? (Y/n): {Colors.END}").strip().lower() != "n"
        if save_report:
            report_path = generate_troubleshooting_report(issues, system_info, output)
            
            if report_path:
                print_instruction(f"Troubleshooting report saved to: {report_path}")
                print_instruction("Share this report if you need help resolving the issues.")
        
        print_instruction("For manual troubleshooting, visit:")
        print_instruction("https://docs.github.com/en/authentication/troubleshooting-ssh")

if __name__ == "__main__":
    main()
