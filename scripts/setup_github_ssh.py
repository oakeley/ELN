#!/usr/bin/env python3
"""
GitHub SSH Setup Script for Electronic Laboratory Notebook

This script helps users set up SSH authentication for GitHub by:
1. Checking if SSH keys already exist
2. Generating new SSH keys if needed
3. Providing instructions for adding the key to GitHub
4. Testing the SSH connection to GitHub
"""

import os
import sys
import subprocess
import platform
import webbrowser
from pathlib import Path

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

def check_ssh_keys():
    """Check if SSH keys already exist"""
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
        "github_rsa", "github_rsa.pub"
    ]
    
    found_keys = []
    for key_file in key_files:
        if (ssh_dir / key_file).exists():
            if key_file.endswith(".pub"):
                private_key = key_file[:-4]
                if (ssh_dir / private_key).exists():
                    found_keys.append((private_key, key_file))
    
    return found_keys

def generate_ssh_key(key_name="id_ed25519", email=""):
    """Generate a new SSH key"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    
    if not ssh_dir.exists():
        ssh_dir.mkdir(mode=0o700)
    
    key_path = ssh_dir / key_name
    if key_path.exists():
        print_warning(f"Key {key_path} already exists. Skipping generation.")
        return False
    
    if not email:
        email = input(f"{Colors.YELLOW}Enter your GitHub email: {Colors.END}")
    
    try:
        subprocess.run([
            "ssh-keygen", 
            "-t", "ed25519" if "ed25519" in key_name else "rsa",
            "-C", email,
            "-f", str(key_path),
            "-N", ""  # Empty passphrase
        ], check=True)
        
        print_success(f"SSH key generated: {key_path}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to generate SSH key: {e}")
        return False

def get_public_key(key_name="id_ed25519"):
    """Get the content of a public key"""
    home_dir = Path.home()
    pub_key_path = home_dir / ".ssh" / f"{key_name}.pub"
    
    if not pub_key_path.exists():
        print_error(f"Public key {pub_key_path} not found.")
        return None
    
    with open(pub_key_path, "r") as f:
        return f.read().strip()

def copy_to_clipboard(text):
    """Copy text to clipboard based on platform"""
    try:
        if platform.system() == "Windows":
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        elif platform.system() == "Linux":
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
        else:
            return False
        return True
    except:
        return False

def configure_ssh_config():
    """Ensure SSH config has GitHub settings"""
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    config_path = ssh_dir / "config"
    
    github_config = """
# GitHub.com
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
"""
    
    if config_path.exists():
        with open(config_path, "r") as f:
            current_config = f.read()
        
        if "github.com" in current_config:
            print_success("GitHub configuration already exists in SSH config.")
            return True
    
    try:
        with open(config_path, "a+") as f:
            f.write(github_config)
        
        os.chmod(config_path, 0o600)  # Set proper permissions
        print_success("Added GitHub configuration to SSH config.")
        return True
    except Exception as e:
        print_error(f"Failed to configure SSH config: {e}")
        return False

def test_github_connection():
    """Test SSH connection to GitHub"""
    print_instruction("Testing connection to GitHub...")
    
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "StrictHostKeyChecking=no", "git@github.com"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        
        # GitHub returns non-zero status even for successful auth
        if "successfully authenticated" in result.stderr:
            print_success("Successfully connected to GitHub!")
            return True
        else:
            print_error("GitHub SSH authentication failed.")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Failed to test GitHub connection: {e}")
        return False

def main():
    """Main function"""
    print_header("GitHub SSH Setup for Electronic Laboratory Notebook")
    
    # Step 1: Check for existing SSH keys
    print_step(1, "Checking for existing SSH keys")
    existing_keys = check_ssh_keys()
    
    if existing_keys:
        print_success(f"Found existing SSH key pairs: {', '.join([k[0] for k in existing_keys])}")
        
        use_existing = input(f"{Colors.YELLOW}Use existing keys? (Y/n): {Colors.END}").strip().lower()
        if use_existing != "n":
            key_to_use = existing_keys[0][0]  # Default to first key
            if len(existing_keys) > 1:
                print("Multiple keys found. Which one would you like to use?")
                for i, (private, public) in enumerate(existing_keys):
                    print(f"{i+1}. {private}")
                
                choice = input(f"{Colors.YELLOW}Enter number (1-{len(existing_keys)}): {Colors.END}").strip()
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(existing_keys):
                        key_to_use = existing_keys[choice_idx][0]
                except:
                    pass  # Use default key if input is invalid
            
            pub_key = get_public_key(key_to_use)
        else:
            # Generate a new key
            print_step(2, "Generating a new SSH key")
            email = input(f"{Colors.YELLOW}Enter your GitHub email: {Colors.END}")
            generate_ssh_key("id_ed25519", email)
            key_to_use = "id_ed25519"
            pub_key = get_public_key(key_to_use)
    else:
        # No existing keys, generate new ones
        print_step(2, "Generating a new SSH key")
        email = input(f"{Colors.YELLOW}Enter your GitHub email: {Colors.END}")
        generate_ssh_key("id_ed25519", email)
        key_to_use = "id_ed25519"
        pub_key = get_public_key(key_to_use)
    
    # Step 3: Update SSH config
    print_step(3, "Configuring SSH settings")
    configure_ssh_config()
    
    # Step 4: Add key to GitHub
    print_step(4, "Adding SSH key to GitHub")
    print("Your public SSH key is:")
    print(f"\n{Colors.BOLD}{pub_key}{Colors.END}\n")
    
    if copy_to_clipboard(pub_key):
        print_success("Public key copied to clipboard!")
    
    print_instruction("1. Go to GitHub Settings → SSH and GPG keys → New SSH key")
    print_instruction("2. Give your key a title (e.g., 'ELN Key')")
    print_instruction("3. Paste the key copied above")
    print_instruction("4. Click 'Add SSH key'")
    
    open_browser = input(f"{Colors.YELLOW}Open GitHub SSH settings in browser? (Y/n): {Colors.END}").strip().lower()
    if open_browser != "n":
        webbrowser.open("https://github.com/settings/ssh/new")
    
    input(f"\n{Colors.YELLOW}Press Enter when you've added the key to GitHub...{Colors.END}")
    
    # Step 5: Test connection
    print_step(5, "Testing GitHub SSH connection")
    success = test_github_connection()
    
    if success:
        print_header("Setup Complete!")
        print(f"Your SSH key is set up and working. Update your .env file with these settings:")
        print(f"""
GITHUB_USERNAME=your-github-username
GITHUB_SSH_KEY_PATH=~/.ssh/{key_to_use}
GITHUB_SSH_PUB_KEY_PATH=~/.ssh/{key_to_use}.pub
""")
    else:
        print_header("Setup Incomplete")
        print_warning("SSH connection test failed. Please check your GitHub settings.")
        print_instruction("For troubleshooting, visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection")

if __name__ == "__main__":
    main()
