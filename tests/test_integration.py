import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models import User, Project, File, FileVersion
from app.github_integration import GitHubIntegration
from app.neo4j_integration import Neo4jIntegration
from app.ollama_integration import OllamaIntegration
from app.latex_export import LatexExport
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = tempfile.mkdtemp()
    GITHUB_USERNAME = 'test_user'
    GITHUB_SSH_KEY_PATH = os.path.join(tempfile.gettempdir(), 'id_ed25519')
    GITHUB_SSH_PUB_KEY_PATH = os.path.join(tempfile.gettempdir(), 'id_ed25519.pub')


class TestIntegration(unittest.TestCase):
    """Integration tests for the Electronic Laboratory Notebook."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Initialize database
        db.create_all()
        
        # Create test user
        self.test_user = User(username='testuser', email='test@example.com', password_hash='hashed_password')
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test project
        self.test_project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(self.test_project)
        db.session.commit()
        
        # Create test files
        self.test_text_file = File(
            filename='test_file.txt',
            file_path=os.path.join(TestConfig.UPLOAD_FOLDER, 'test_file.txt'),
            file_type='text',
            content='This is test content',
            project_id=self.test_project.id
        )
        db.session.add(self.test_text_file)
        
        # Create a text file on disk
        with open(self.test_text_file.file_path, 'w') as f:
            f.write('This is test content')
        
        # Create a test image file
        self.test_image_file_path = os.path.join(TestConfig.UPLOAD_FOLDER, 'test_image.jpg')
        with open(self.test_image_file_path, 'wb') as f:
            f.write(b'fake image data')
        
        self.test_image_file = File(
            filename='test_image.jpg',
            file_path=self.test_image_file_path,
            file_type='image',
            project_id=self.test_project.id
        )
        db.session.add(self.test_image_file)
        db.session.commit()
        
        # Set up session for authentication
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user.id
            session['username'] = self.test_user.username
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Clean up test files
        if os.path.exists(TestConfig.UPLOAD_FOLDER):
            shutil.rmtree(TestConfig.UPLOAD_FOLDER)
    
    @patch('app.neo4j_integration.Neo4jIntegration.create_project_node')
    @patch('app.neo4j_integration.Neo4jIntegration.create_file_node')
    def test_project_file_integration(self, mock_create_file_node, mock_create_project_node):
        """Test the integration between projects and files."""
        # Mock Neo4j integration
        mock_create_project_node.return_value = {'project_id': 1}
        mock_create_file_node.return_value = {'file_id': 1}
        
        # Create a new project
        response = self.client.post('/api/projects', json={
            'name': 'Integration Test Project',
            'description': 'Project for integration testing'
        })
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        project_id = data['project']['id']
        
        # Verify Neo4j was called for project creation
        mock_create_project_node.assert_called_once()
        
        # Create a new text file in the project
        response = self.client.post(f'/api/projects/{project_id}/files', data={
            'filename': 'integration_test.txt',
            'content': 'This is content for integration testing'
        })
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        file_id = data['file']['id']
        
        # Verify Neo4j was called for file creation
        mock_create_file_node.assert_called_once()
        
        # Retrieve the file
        response = self.client.get(f'/api/files/{file_id}')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['filename'], 'integration_test.txt')
        self.assertEqual(data['file']['content'], 'This is content for integration testing')
        
        # Update the file
        response = self.client.put(f'/api/files/{file_id}', json={
            'content': 'Updated content for integration testing',
            'commit_message': 'Update for integration test'
        })
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Verify file was updated
        response = self.client.get(f'/api/files/{file_id}')
        data = response.get_json()
        self.assertEqual(data['file']['content'], 'Updated content for integration testing')
        
        # Check that a new version was created
        self.assertGreaterEqual(len(data['file']['versions']), 1)
    
    @patch('app.github_integration.GitHubIntegration.verify_ssh_setup')
    @patch('app.github_integration.GitHubIntegration.publish_project_to_github')
    def test_github_integration(self, mock_publish, mock_verify_ssh):
        """Test the integration with GitHub."""
        # Mock SSH verification
        mock_verify_ssh.return_value = {'success': True}
        
        # Mock GitHub publish
        mock_publish.return_value = {
            'success': True,
            'repo_name': 'eln-test-project',
            'full_name': 'test_user/eln-test-project',
            'html_url': 'https://github.com/test_user/eln-test-project',
            'ssh_url': 'git@github.com:test_user/eln-test-project.git'
        }
        
        # Verify SSH setup
        response = self.client.get('/api/github/verify-ssh')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Publish project to GitHub
        response = self.client.post(f'/api/projects/{self.test_project.id}/github/publish')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['github']['repo_name'], 'eln-test-project')
        self.assertEqual(data['github']['full_name'], 'test_user/eln-test-project')
        
        # Verify project was updated with GitHub repo info
        project = Project.query.get(self.test_project.id)
        self.assertEqual(project.github_repo, 'test_user/eln-test-project')
    
    @patch('app.ollama_integration.OllamaIntegration.extract_keywords')
    @patch('app.ollama_integration.OllamaIntegration.search_projects')
    def test_ollama_integration(self, mock_search, mock_extract):
        """Test the integration with Ollama AI model."""
        # Mock keyword extraction
        mock_extract.return_value = {
            'success': True,
            'keywords': ['test', 'integration', 'electronic', 'notebook']
        }
        
        # Mock search results
        mock_search.return_value = {
            'success': True,
            'results': [
                {
                    'project': {
                        'id': self.test_project.id,
                        'name': 'Test Project',
                        'description': 'This is a test project',
                        'files': [
                            {
                                'id': self.test_text_file.id,
                                'filename': 'test_file.txt',
                                'file_type': 'text'
                            }
                        ]
                    },
                    'relevance_score': 8.5
                }
            ]
        }
        
        # Test keyword extraction during file creation
        with patch('app.neo4j_integration.Neo4jIntegration.add_keyword_to_file') as mock_add_keyword:
            response = self.client.post(f'/api/projects/{self.test_project.id}/files', data={
                'filename': 'ollama_test.txt',
                'content': 'This is content for Ollama testing'
            })
            
            self.assertEqual(response.status_code, 200)
            mock_extract.assert_called_once()
            mock_add_keyword.assert_called()
        
        # Test search functionality
        response = self.client.get('/api/search?q=electronic%20notebook')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['project']['id'], self.test_project.id)
        self.assertIsInstance(data['results'][0]['relevance_score'], float)
    
    @patch('app.latex_export.LatexExport.generate_latex')
    @patch('app.latex_export.LatexExport.generate_pdf')
    def test_latex_pdf_export(self, mock_generate_pdf, mock_generate_latex):
        """Test the PDF export via LaTeX."""
        # Mock LaTeX generation
        mock_generate_latex.return_value = '\\documentclass{article}\\begin{document}Test content\\end{document}'
        
        # Mock PDF generation
        mock_generate_pdf.return_value = {
            'success': True,
            'pdf_content': b'Fake PDF content'
        }
        
        # Test PDF export
        response = self.client.get(f'/api/projects/{self.test_project.id}/export/pdf')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertEqual(response.headers['Content-Disposition'], f'attachment; filename={self.test_project.name}.pdf')
        
        # Verify LaTeX and PDF generation were called
        mock_generate_latex.assert_called_once()
        mock_generate_pdf.assert_called_once()
    
    @patch('app.ollama_integration.OllamaIntegration.enhance_image_to_line_art')
    def test_image_enhancement(self, mock_enhance):
        """Test image enhancement with Ollama."""
        # Mock image enhancement
        mock_enhance.return_value = {
            'success': True,
            'file_path': os.path.join(TestConfig.UPLOAD_FOLDER, 'enhanced_test_image.jpg')
        }
        
        # Create an enhanced image file
        enhanced_path = os.path.join(TestConfig.UPLOAD_FOLDER, 'enhanced_test_image.jpg')
        with open(enhanced_path, 'wb') as f:
            f.write(b'fake enhanced image data')
        
        # Test image enhancement
        response = self.client.post(f'/api/files/{self.test_image_file.id}/enhance', json={
            'type': 'ollama'
        })
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['file_type'], 'image')
        self.assertTrue('enhanced' in data['file']['filename'])
        
        # Verify enhancement was called
        mock_enhance.assert_called_once_with(
            self.test_image_file.file_path,
            os.path.join(TestConfig.UPLOAD_FOLDER, data['file']['filename'])
        )
    
    def test_end_to_end_workflow(self):
        """Test an end-to-end workflow with mocked external services."""
        # Mock all external services
        with patch('app.neo4j_integration.Neo4jIntegration.create_project_node'), \
             patch('app.neo4j_integration.Neo4jIntegration.create_file_node'), \
             patch('app.ollama_integration.OllamaIntegration.extract_keywords', return_value={'success': True, 'keywords': ['test']}), \
             patch('app.neo4j_integration.Neo4jIntegration.add_keyword_to_file'), \
             patch('app.github_integration.GitHubIntegration.verify_ssh_setup', return_value={'success': True}), \
             patch('app.github_integration.GitHubIntegration.publish_project_to_github', return_value={
                'success': True,
                'repo_name': 'eln-workflow-test',
                'full_name': 'test_user/eln-workflow-test',
                'html_url': 'https://github.com/test_user/eln-workflow-test',
                'ssh_url': 'git@github.com:test_user/eln-workflow-test.git'
             }), \
             patch('app.latex_export.LatexExport.export_project_to_pdf', return_value={
                'success': True,
                'pdf_content': b'Fake PDF content'
             }):
                
                # 1. Create a new project
                response = self.client.post('/api/projects', json={
                    'name': 'Workflow Test Project',
                    'description': 'End-to-end workflow test'
                })
                project_data = response.get_json()
                project_id = project_data['project']['id']
                
                # 2. Add a text file
                response = self.client.post(f'/api/projects/{project_id}/files', data={
                    'filename': 'workflow_test.txt',
                    'content': 'This is a test file for the end-to-end workflow'
                })
                file_data = response.get_json()
                file_id = file_data['file']['id']
                
                # 3. Update the file
                response = self.client.put(f'/api/files/{file_id}', json={
                    'content': 'Updated content for the workflow test',
                    'commit_message': 'Update for workflow test'
                })
                self.assertTrue(response.get_json()['success'])
                
                # 4. Publish to GitHub
                response = self.client.post(f'/api/projects/{project_id}/github/publish')
                github_data = response.get_json()
                self.assertTrue(github_data['success'])
                
                # 5. Export to PDF
                response = self.client.get(f'/api/projects/{project_id}/export/pdf')
                self.assertEqual(response.status_code, 200)
                
                # 6. Verify the project in the database
                project = Project.query.get(project_id)
                self.assertEqual(project.name, 'Workflow Test Project')
                self.assertEqual(project.github_repo, 'test_user/eln-workflow-test')
                
                # 7. Verify the file in the database
                file = File.query.get(file_id)
                self.assertEqual(file.filename, 'workflow_test.txt')
                self.assertEqual(file.content, 'Updated content for the workflow test')
                
                # 8. Verify file versions
                self.assertGreaterEqual(file.versions.count(), 1)


if __name__ == '__main__':
    unittest.main()
