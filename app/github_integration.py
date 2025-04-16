from github import Github
from flask import current_app
import os
import base64

class GitHubIntegration:
    def __init__(self):
        """Initialize GitHub API connection using app configuration"""
        self.token = current_app.config['GITHUB_TOKEN']
        self.github = Github(self.token)
        self.user = self.github.get_user()
    
    def create_repository(self, name, description="Electronic Laboratory Notebook Project", private=True):
        """Create a new GitHub repository"""
        try:
            repo = self.user.create_repo(name=name, description=description, private=private)
            return {
                'success': True,
                'repo_name': repo.name,
                'full_name': repo.full_name,
                'html_url': repo.html_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_repository_exists(self, repo_name):
        """Check if a repository exists for the authenticated user"""
        try:
            repos = self.user.get_repos()
            for repo in repos:
                if repo.name == repo_name:
                    return True
            return False
        except Exception as e:
            return False
    
    def get_repository(self, full_name):
        """Get a repository by its full name"""
        try:
            repo = self.github.get_repo(full_name)
            return repo
        except Exception as e:
            return None
    
    def delete_repository(self, full_name):
        """Delete a GitHub repository"""
        try:
            repo = self.github.get_repo(full_name)
            repo.delete()
            return {
                'success': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_file_to_repo(self, repo_full_name, file_path, content, commit_message="Add file"):
        """Upload a file to a GitHub repository"""
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Check if file exists
            try:
                file_content = repo.get_contents(file_path)
                # Update file
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=file_content.sha
                )
            except:
                # Create file
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content
                )
            
            return {
                'success': True,
                'file_path': file_path
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_binary_file_to_repo(self, repo_full_name, file_path, binary_content, commit_message="Add binary file"):
        """Upload a binary file (image, etc.) to a GitHub repository"""
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Encode binary content to base64
            encoded_content = base64.b64encode(binary_content).decode('utf-8')
            
            # Check if file exists
            try:
                file_content = repo.get_contents(file_path)
                # Update file
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=encoded_content,
                    sha=file_content.sha
                )
            except:
                # Create file
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=encoded_content
                )
            
            return {
                'success': True,
                'file_path': file_path
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file_from_repo(self, repo_full_name, file_path):
        """Download a file from a GitHub repository"""
        try:
            repo = self.github.get_repo(repo_full_name)
            contents = repo.get_contents(file_path)
            
            if isinstance(contents, list):
                return {
                    'success': False,
                    'error': 'Path is a directory, not a file'
                }
            
            content = contents.decoded_content
            
            return {
                'success': True,
                'content': content,
                'sha': contents.sha
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_repo_contents(self, repo_full_name, path=""):
        """List contents of a repository directory"""
        try:
            repo = self.github.get_repo(repo_full_name)
            contents = repo.get_contents(path)
            
            items = []
            for content in contents:
                item = {
                    'name': content.name,
                    'path': content.path,
                    'type': 'dir' if content.type == 'dir' else 'file',
                    'sha': content.sha,
                    'url': content.html_url
                }
                items.append(item)
            
            return {
                'success': True,
                'items': items
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def publish_project_to_github(self, project, files):
        """Publish an entire project to GitHub"""
        try:
            # Create or get repository
            repo_name = f"eln-{project.name.lower().replace(' ', '-')}"
            
            if self.check_repository_exists(repo_name):
                repo = self.user.get_repo(repo_name)
                repo_full_name = repo.full_name
            else:
                result = self.create_repository(repo_name, description=project.description)
                if not result['success']:
                    return result
                repo_full_name = result['full_name']
            
            # Upload README with project info
            readme_content = f"# {project.name}\n\n{project.description}\n\n"
            readme_content += f"This is an Electronic Laboratory Notebook project.\n"
            
            self.upload_file_to_repo(
                repo_full_name=repo_full_name,
                file_path="README.md",
                content=readme_content,
                commit_message="Add README"
            )
            
            # Upload all project files
            for file in files:
                file_path = file.filename
                
                if file.file_type == 'text':
                    # Upload text file
                    self.upload_file_to_repo(
                        repo_full_name=repo_full_name,
                        file_path=file_path,
                        content=file.content,
                        commit_message=f"Add {file_path}"
                    )
                else:
                    # Upload binary file
                    with open(file.file_path, 'rb') as f:
                        binary_content = f.read()
                    
                    self.upload_binary_file_to_repo(
                        repo_full_name=repo_full_name,
                        file_path=file_path,
                        binary_content=binary_content,
                        commit_message=f"Add {file_path}"
                    )
            
            # Get repo URL
            repo = self.github.get_repo(repo_full_name)
            
            return {
                'success': True,
                'repo_name': repo.name,
                'full_name': repo_full_name,
                'html_url': repo.html_url
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_project_from_github(self, repo_full_name, user_id):
        """Import a project from GitHub"""
        from app.models import Project, File
        from app import db
        import os
        
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Create project
            project = Project(
                name=repo.name,
                description=repo.description or "Imported from GitHub",
                user_id=user_id,
                github_repo=repo_full_name
            )
            
            db.session.add(project)
            db.session.flush()  # Get project ID without committing
            
            # Get all files from repo
            contents = self.list_repo_contents(repo_full_name)
            
            if not contents['success']:
                db.session.rollback()
                return contents
            
            all_files = []
            for item in contents['items']:
                if item['type'] == 'file':
                    file_result = self.download_file_from_repo(repo_full_name, item['path'])
                    
                    if file_result['success']:
                        content = file_result['content']
                        
                        # Determine file type
                        name, ext = os.path.splitext(item['name'])
                        file_type = 'text'
                        text_content = None
                        
                        if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                            file_type = 'image'
                        else:
                            try:
                                text_content = content.decode('utf-8')
                            except UnicodeDecodeError:
                                file_type = 'binary'
                        
                        # Save the file locally
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        file_path = os.path.join(upload_folder, item['name'])
                        
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        # Create file record
                        file = File(
                            filename=item['name'],
                            file_path=file_path,
                            file_type=file_type,
                            content=text_content,
                            project_id=project.id
                        )
                        
                        db.session.add(file)
                        all_files.append(file)
            
            db.session.commit()
            
            return {
                'success': True,
                'project': project,
                'files': all_files
            }
        
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
