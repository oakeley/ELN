import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app import create_app
from app.github_integration import GitHubIntegration
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    GITHUB_USERNAME = 'test_user'
    GITHUB_SSH_KEY_PATH = os.path.join(tempfile.gettempdir(), 'id_ed25519')
    GITHUB_SSH_PUB_KEY_PATH = os.path.join(tempfile.gettempdir(), 'id_ed25519.pub')
    GIT_USER_NAME = 'Test User'
    GIT_USER_EMAIL = 'test@example.com'


class TestGitHubIntegration(unittest.TestCase):
    """Test cases for GitHub integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test SSH keys
        with open(TestConfig.GITHUB_SSH_KEY_PATH, 'w') as f:
            f.write('Mock SSH private key content')
        with open(TestConfig.GITHUB_SSH_PUB_KEY_PATH, 'w') as f:
            f.write('Mock SSH public key content')
        
        self.github_integration = GitHubIntegration()
        
        # Create a temp directory to simulate Git operations
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()
        
        # Clean up test SSH keys
        if os.path.exists(TestConfig.GITHUB_SSH_KEY_PATH):
            os.remove(TestConfig.GITHUB_SSH_KEY_PATH)
        if os.path.exists(TestConfig.GITHUB_SSH_PUB_KEY_PATH):
            os.remove(TestConfig.GITHUB_SSH_PUB_KEY_PATH)
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_verify_ssh_setup(self, mock_run):
        """Test SSH setup verification."""
        # Mock successful SSH connection
        mock_process = MagicMock()
        mock_process.stderr = 'Hi test_user! You have successfully authenticated'
        mock_run.return_value = mock_process
        
        result = self.github_integration.verify_ssh_setup()
        self.assertTrue(result['success'])
        
        # Mock failed SSH connection
        mock_process.stderr = 'Permission denied (publickey)'
        result = self.github_integration.verify_ssh_setup()
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    def test_create_repository_with_github_cli(self, mock_run):
        """Test repository creation with GitHub CLI."""
        # Mock successful repository creation
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Set github API to None to force using CLI
        self.github_integration.github = None
        
        result = self.github_integration.create_repository('test-repo', 'Test repository', True)
        self.assertTrue(result['success'])
        self.assertEqual(result['repo_name'], 'test-repo')
        self.assertEqual(result['full_name'], 'test_user/test-repo')
        self.assertEqual(result['html_url'], 'https://github.com/test_user/test-repo')
        self.assertEqual(result['ssh_url'], 'git@github.com:test_user/test-repo.git')
        
        # Mock failed repository creation
        mock_process.returncode = 1
        mock_process.stderr = 'Error creating repository'
        result = self.github_integration.create_repository('test-repo', 'Test repository', True)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    def test_check_repository_exists(self, mock_run):
        """Test repository existence check."""
        # Mock existing repository
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Set github API to None to force using CLI
        self.github_integration.github = None
        
        exists = self.github_integration.check_repository_exists('existing-repo')
        self.assertTrue(exists)
        
        # Mock non-existing repository
        mock_process.returncode = 1
        exists = self.github_integration.check_repository_exists('non-existing-repo')
        self.assertFalse(exists)
    
    @patch('subprocess.run')
    @patch('json.loads')
    def test_get_repository_details(self, mock_json_loads, mock_run):
        """Test repository details retrieval."""
        # Mock successful repository details retrieval
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '{"name": "test-repo", "description": "Test repo", "url": "https://github.com/test_user/test-repo", "sshUrl": "git@github.com:test_user/test-repo.git"}'
        mock_run.return_value = mock_process
        
        # Use real JSON loading
        mock_json_loads.side_effect = lambda x: {"name": "test-repo", "description": "Test repo", "url": "https://github.com/test_user/test-repo", "sshUrl": "git@github.com:test_user/test-repo.git"}
        
        result = self.github_integration.get_repository_details('test-repo')
        self.assertTrue(result['success'])
        self.assertEqual(result['repo_name'], 'test-repo')
        self.assertEqual(result['full_name'], 'test_user/test-repo')
        self.assertEqual(result['description'], 'Test repo')
        self.assertEqual(result['html_url'], 'https://github.com/test_user/test-repo')
        self.assertEqual(result['ssh_url'], 'git@github.com:test_user/test-repo.git')
        
        # Mock failed repository details retrieval
        mock_process.returncode = 1
        mock_process.stderr = 'Error retrieving repository details'
        result = self.github_integration.get_repository_details('non-existing-repo')
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    def test_delete_repository(self, mock_run):
        """Test repository deletion."""
        # Mock successful repository deletion
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Set github API to None to force using CLI
        self.github_integration.github = None
        
        result = self.github_integration.delete_repository('test-repo')
        self.assertTrue(result['success'])
        
        # Mock failed repository deletion
        mock_process.returncode = 1
        mock_process.stderr = 'Error deleting repository'
        result = self.github_integration.delete_repository('non-existing-repo')
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_publish_project_to_github(self, mock_rmtree, mock_mkdtemp, mock_exists, mock_run):
        """Test project publishing to GitHub."""
        # Mock project and files
        project = MagicMock()
        project.name = 'Test Project'
        project.description = 'Test project description'
        
        file1 = MagicMock()
        file1.filename = 'test_file.txt'
        file1.file_type = 'text'
        file1.content = 'Test content'
        
        file2 = MagicMock()
        file2.filename = 'test_image.jpg'
        file2.file_type = 'image'
        file2.file_path = '/path/to/test_image.jpg'
        
        files = [file1, file2]
        
        # Mock file operations
        mock_exists.return_value = True
        mock_mkdtemp.return_value = self.temp_dir
        
        # Mock Git operations
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock repository check and creation
        self.github_integration.check_repository_exists = MagicMock(return_value=False)
        self.github_integration.create_repository = MagicMock(return_value={
            'success': True,
            'repo_name': 'eln-test-project',
            'full_name': 'test_user/eln-test-project',
            'html_url': 'https://github.com/test_user/eln-test-project',
            'ssh_url': 'git@github.com:test_user/eln-test-project.git'
        })
        
        # Test project publishing
        result = self.github_integration.publish_project_to_github(project, files)
        self.assertTrue(result['success'])
        self.assertEqual(result['repo_name'], 'eln-test-project')
        self.assertEqual(result['full_name'], 'test_user/eln-test-project')
        self.assertEqual(result['html_url'], 'https://github.com/test_user/eln-test-project')
        self.assertEqual(result['ssh_url'], 'git@github.com:test_user/eln-test-project.git')
        
        # Test failure during Git operations
        mock_process.returncode = 1
        mock_process.stderr = 'Error pushing to GitHub'
        self.github_integration.check_repository_exists = MagicMock(return_value=False)
        self.github_integration.create_repository = MagicMock(return_value={
            'success': True,
            'repo_name': 'eln-test-project',
            'full_name': 'test_user/eln-test-project',
            'html_url': 'https://github.com/test_user/eln-test-project',
            'ssh_url': 'git@github.com:test_user/eln-test-project.git'
        })
        
        result = self.github_integration.publish_project_to_github(project, files)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    @patch('shutil.copy2')
    @patch('os.walk')
    def test_import_project_from_github(self, mock_walk, mock_copy2, mock_rmtree, mock_mkdtemp, mock_exists, mock_run):
        """Test project import from GitHub."""
        # Mock file system
        mock_exists.return_value = True
        mock_mkdtemp.return_value = self.temp_dir
        
        # Mock Git operations
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock file discovery
        mock_walk.return_value = [
            (self.temp_dir, [], ['README.md', 'test_file.txt', 'test_image.jpg']),
        ]
        
        # Mock database and models
        with patch('app.github_integration.Project') as MockProject, \
             patch('app.github_integration.File') as MockFile, \
             patch('app.github_integration.db') as mock_db:
            
            # Set up mock objects
            mock_project = MagicMock()
            mock_project.id = 1
            MockProject.return_value = mock_project
            
            mock_file = MagicMock()
            mock_file.id = 1
            MockFile.return_value = mock_file
            
            # Test import with HTTPS URL
            result = self.github_integration.import_project_from_github('https://github.com/test_user/test-repo', 1)
            self.assertTrue(result['success'])
            self.assertEqual(result['project'], mock_project)
            self.assertIn('files', result)
            
            # Test import with SSH URL
            result = self.github_integration.import_project_from_github('git@github.com:test_user/test-repo.git', 1)
            self.assertTrue(result['success'])
            self.assertEqual(result['project'], mock_project)
            self.assertIn('files', result)
            
            # Test import with username/repo format
            result = self.github_integration.import_project_from_github('test_user/test-repo', 1)
            self.assertTrue(result['success'])
            self.assertEqual(result['project'], mock_project)
            self.assertIn('files', result)
            
            # Test import with just repo name
            result = self.github_integration.import_project_from_github('test-repo', 1)
            self.assertTrue(result['success'])
            self.assertEqual(result['project'], mock_project)
            self.assertIn('files', result)
            
            # Test import failure
            mock_process.returncode = 1
            mock_process.stderr = 'Error cloning repository'
            
            mock_db.session.rollback = MagicMock()
            
            result = self.github_integration.import_project_from_github('non-existing-repo', 1)
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            mock_db.session.rollback.assert_called_once()


if __name__ == '__main__':
    unittest.main()
