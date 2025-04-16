from github import Github
from flask import current_app
import os
import base64
import subprocess
import tempfile
import re
import shutil

class GitHubIntegration:
    def __init__(self):
        """Initialize GitHub integration using SSH authentication"""
        self.ssh_key_path = current_app.config.get('GITHUB_SSH_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa'))
        self.ssh_pub_key_path = current_app.config.get('GITHUB_SSH_PUB_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa.pub'))
        self.github_username = current_app.config.get('GITHUB_USERNAME', '')
        
        # For API calls that require PyGithub
        # Use username/token auth for API only (if available)
        self.token = current_app.config.get('GITHUB_TOKEN', '')
        if self.token:
            self.github = Github(self.token)
            self.user = self.github.get_user()
        else:
            self.github = None
            self.user = None
    
    def verify_ssh_setup(self):
        """Verify that SSH keys are set up for GitHub authentication"""
        # Check if SSH key exists
        if not os.path.exists(self.ssh_key_path) or not os.path.exists(self.ssh_pub_key_path):
            return {
                'success': False,
                'error': 'SSH keys not found. Please generate them with ssh-keygen and add to GitHub.'
            }
        
        # Test SSH connection to GitHub
        try:
            result = subprocess.run(
                ['ssh', '-T', '-o', 'StrictHostKeyChecking=no', 'git@github.com'],
                capture_output=True,
                text=True
            )
            
            # GitHub returns non-zero exit code even when successful, so check output
            if 'successfully authenticated' in result.stderr:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f'GitHub SSH authentication failed: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error testing SSH connection: {str(e)}'
            }
    
    def create_repository(self, name, description="Electronic Laboratory Notebook Project", private=True):
        """Create a new GitHub repository"""
        if self.github and self.user:
            # Use PyGithub API if token is available
            try:
                repo = self.user.create_repo(name=name, description=description, private=private)
                return {
                    'success': True,
                    'repo_name': repo.name,
                    'full_name': repo.full_name,
                    'html_url': repo.html_url,
                    'ssh_url': repo.ssh_url
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            # Use GitHub CLI if available
            try:
                visibility = '--private' if private else '--public'
                result = subprocess.run(
                    ['gh', 'repo', 'create', name, visibility, '--description', description, '--confirm'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Extract repository URL from output
                    ssh_url = f"git@github.com:{self.github_username}/{name}.git"
                    html_url = f"https://github.com/{self.github_username}/{name}"
                    
                    return {
                        'success': True,
                        'repo_name': name,
                        'full_name': f"{self.github_username}/{name}",
                        'html_url': html_url,
                        'ssh_url': ssh_url
                    }
                else:
                    return {
                        'success': False,
                        'error': result.stderr
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error creating repository: {str(e)}. Make sure GitHub CLI is installed.'
                }
    
    def check_repository_exists(self, repo_name):
        """Check if a repository exists for the authenticated user"""
        if self.github and self.user:
            # Use PyGithub API if token is available
            try:
                repos = self.user.get_repos()
                for repo in repos:
                    if repo.name == repo_name:
                        return True
                return False
            except Exception:
                return False
        else:
            # Use GitHub CLI
            try:
                result = subprocess.run(
                    ['gh', 'repo', 'view', f"{self.github_username}/{repo_name}"],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except Exception:
                return False
    
    def get_repository_details(self, repo_name):
        """Get repository details using GitHub CLI"""
        try:
            result = subprocess.run(
                ['gh', 'repo', 'view', f"{self.github_username}/{repo_name}", '--json', 'name,description,sshUrl,url'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                repo_data = json.loads(result.stdout)
                return {
                    'success': True,
                    'repo_name': repo_data['name'],
                    'full_name': f"{self.github_username}/{repo_data['name']}",
                    'description': repo_data.get('description', ''),
                    'html_url': repo_data['url'],
                    'ssh_url': repo_data['sshUrl']
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_repository(self, repo_name):
        """Delete a GitHub repository"""
        if self.github and self.user:
            # Use PyGithub API if token is available
            try:
                full_name = f"{self.user.login}/{repo_name}"
                repo = self.github.get_repo(full_name)
                repo.delete()
                return {'success': True}
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            # Use GitHub CLI
            try:
                result = subprocess.run(
                    ['gh', 'repo', 'delete', f"{self.github_username}/{repo_name}", '--yes'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': result.stderr
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def publish_project_to_github(self, project, files):
        """Publish an entire project to GitHub using Git and SSH"""
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Initialize git repo in temp directory
                subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
                
                # Configure git user (use ELN as author if not specified in config)
                git_user_name = current_app.config.get('GIT_USER_NAME', 'Electronic Lab Notebook')
                git_user_email = current_app.config.get('GIT_USER_EMAIL', 'eln@example.com')
                
                subprocess.run(['git', 'config', 'user.name', git_user_name], cwd=temp_dir, check=True, capture_output=True)
                subprocess.run(['git', 'config', 'user.email', git_user_email], cwd=temp_dir, check=True, capture_output=True)
                
                # Create or get repository
                repo_name = f"eln-{project.name.lower().replace(' ', '-')}"
                repo_exists = self.check_repository_exists(repo_name)
                
                if repo_exists:
                    repo_details = self.get_repository_details(repo_name)
                    if not repo_details['success']:
                        return repo_details
                    ssh_url = repo_details['ssh_url']
                    full_name = repo_details['full_name']
                    html_url = repo_details['html_url']
                else:
                    result = self.create_repository(repo_name, description=project.description, private=True)
                    if not result['success']:
                        return result
                    ssh_url = result['ssh_url']
                    full_name = result['full_name']
                    html_url = result['html_url']
                
                # Add remote
                subprocess.run(['git', 'remote', 'add', 'origin', ssh_url], cwd=temp_dir, check=True, capture_output=True)
                
                # Create README.md with project info
                readme_content = f"# {project.name}\n\n{project.description}\n\n"
                readme_content += f"This is an Electronic Laboratory Notebook project.\n"
                
                with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
                    f.write(readme_content)
                
                # Add and commit files
                for file in files:
                    file_path = os.path.join(temp_dir, file.filename)
                    
                    if file.file_type == 'text':
                        # Write text file
                        with open(file_path, 'w') as f:
                            f.write(file.content or '')
                    else:
                        # Copy binary file
                        shutil.copy2(file.file_path, file_path)
                
                # Add all files to git
                subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True, capture_output=True)
                
                # Commit changes
                subprocess.run(
                    ['git', 'commit', '-m', f"Publish project: {project.name}"],
                    cwd=temp_dir, check=True, capture_output=True
                )
                
                # Push to GitHub using SSH
                push_result = subprocess.run(
                    ['git', 'push', '-u', 'origin', 'main'],
                    cwd=temp_dir, capture_output=True, text=True
                )
                
                if push_result.returncode != 0:
                    # Try pushing to master branch if main fails
                    push_result = subprocess.run(
                        ['git', 'push', '-u', 'origin', 'master'],
                        cwd=temp_dir, capture_output=True, text=True
                    )
                
                if push_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f"Failed to push to GitHub: {push_result.stderr}"
                    }
                
                return {
                    'success': True,
                    'repo_name': repo_name,
                    'full_name': full_name,
                    'html_url': html_url,
                    'ssh_url': ssh_url
                }
                
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_project_from_github(self, repo_name_or_url, user_id):
        """Import a project from GitHub using Git and SSH"""
        from app.models import Project, File
        from app import db
        
        # Extract repo name from URL if provided
        if '/' in repo_name_or_url:
            # Handle SSH URL: git@github.com:username/repo.git
            if repo_name_or_url.startswith('git@github.com:'):
                match = re.search(r'git@github\.com:([^/]+)/([^.]+)\.git', repo_name_or_url)
                if match:
                    username, repo_name = match.groups()
                else:
                    return {
                        'success': False,
                        'error': 'Invalid GitHub SSH URL format'
                    }
            # Handle HTTPS URL: https://github.com/username/repo
            elif 'github.com' in repo_name_or_url:
                match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_name_or_url)
                if match:
                    username, repo_name = match.groups()
                else:
                    return {
                        'success': False,
                        'error': 'Invalid GitHub URL format'
                    }
            else:
                # Assume username/repo format
                parts = repo_name_or_url.split('/')
                if len(parts) == 2:
                    username, repo_name = parts
                else:
                    return {
                        'success': False,
                        'error': 'Invalid repository format. Use "username/repo" or a GitHub URL.'
                    }
        else:
            # Just a repo name, assume it belongs to the configured username
            repo_name = repo_name_or_url
            username = self.github_username
        
        # Use SSH URL format
        ssh_url = f"git@github.com:{username}/{repo_name}.git"
        html_url = f"https://github.com/{username}/{repo_name}"
        full_name = f"{username}/{repo_name}"
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Clone the repository
                clone_result = subprocess.run(
                    ['git', 'clone', ssh_url, temp_dir],
                    capture_output=True,
                    text=True
                )
                
                if clone_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f"Failed to clone repository: {clone_result.stderr}"
                    }
                
                # Create project
                project = Project(
                    name=repo_name,
                    description=f"Imported from GitHub: {full_name}",
                    user_id=user_id,
                    github_repo=full_name
                )
                
                db.session.add(project)
                db.session.flush()  # Get project ID without committing
                
                # Process all files in the repo
                all_files = []
                
                for root, _, filenames in os.walk(temp_dir):
                    # Skip .git directory
                    if '.git' in root:
                        continue
                    
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        
                        # Get relative path from repo root
                        rel_path = os.path.relpath(file_path, temp_dir)
                        
                        # Determine file type
                        file_type = 'binary'
                        content = None
                        
                        # Try to read as text
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                file_type = 'text'
                        except UnicodeDecodeError:
                            # Not a text file, check if it's an image
                            if rel_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                file_type = 'image'
                        
                        # Save file in our storage
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        dest_path = os.path.join(upload_folder, filename)
                        
                        # Copy to upload folder
                        shutil.copy2(file_path, dest_path)
                        
                        # Create file record
                        file = File(
                            filename=rel_path,
                            file_path=dest_path,
                            file_type=file_type,
                            content=content,
                            project_id=project.id
                        )
                        
                        db.session.add(file)
                        all_files.append(file)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'project': project,
                    'files': all_files,
                    'repo': {
                        'name': repo_name,
                        'full_name': full_name,
                        'html_url': html_url,
                        'ssh_url': ssh_url
                    }
                }
                
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
