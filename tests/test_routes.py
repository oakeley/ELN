import unittest
import os
import io
import tempfile
import json
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models import User, Project, File, FileVersion
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = tempfile.mkdtemp()


class TestRoutes(unittest.TestCase):
    """Test cases for API routes."""

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

        # Create test project
        self.test_project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(self.test_project)

        # Create test file
        self.test_file = File(
            filename='test_file.txt',
            file_path=os.path.join(TestConfig.UPLOAD_FOLDER, 'test_file.txt'),
            file_type='text',
            content='This is test content',
            project_id=self.test_project.id
        )
        db.session.add(self.test_file)

        # Create test file version
        self.test_version = FileVersion(
            version_number=1,
            content='This is test content',
            file_path=self.test_file.file_path,
            commit_message='Initial commit',
            file_id=self.test_file.id
        )
        db.session.add(self.test_version)

        db.session.commit()

        # Create a physical file for testing
        with open(self.test_file.file_path, 'w') as f:
            f.write('This is test content')

    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        # Clean up test files
        if os.path.exists(TestConfig.UPLOAD_FOLDER):
            for file in os.listdir(TestConfig.UPLOAD_FOLDER):
                os.remove(os.path.join(TestConfig.UPLOAD_FOLDER, file))

    def login(self):
        """Helper method to log in."""
        with self.client.session_transaction() as session:
            session['user_id'] = self.test_user.id
            session['username'] = self.test_user.username

    def test_index_route(self):
        """Test the index route."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_api_auth_status_not_logged_in(self):
        """Test auth status when not logged in."""
        response = self.client.get('/api/auth/status')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['logged_in'])

    def test_api_auth_status_logged_in(self):
        """Test auth status when logged in."""
        self.login()

        response = self.client.get('/api/auth/status')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['logged_in'])
        self.assertEqual(data['user_id'], self.test_user.id)
        self.assertEqual(data['username'], self.test_user.username)

    @patch('app.routes.verify_password')
    def test_api_auth_login(self, mock_verify):
        """Test login route."""
        # Mock password verification
        mock_verify.return_value = True

        response = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

        # Verify session is set
        with self.client.session_transaction() as session:
            self.assertEqual(session['user_id'], self.test_user.id)
            self.assertEqual(session['username'], self.test_user.username)

    @patch('app.routes.verify_password')
    def test_api_auth_login_invalid(self, mock_verify):
        """Test login route with invalid credentials."""
        # Mock password verification
        mock_verify.return_value = False

        response = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])

    @patch('app.routes.hash_password')
    def test_api_auth_register(self, mock_hash):
        """Test registration route."""
        # Mock password hashing
        mock_hash.return_value = 'hashed_new_password'

        response = self.client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

        # Verify user was created
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.password_hash, 'hashed_new_password')

        # Verify session is set
        with self.client.session_transaction() as session:
            self.assertEqual(session['user_id'], user.id)
            self.assertEqual(session['username'], user.username)

    def test_api_auth_register_existing_user(self):
        """Test registration route with existing username."""
        response = self.client.post('/api/auth/register', json={
            'username': 'testuser',  # Existing username
            'email': 'another@example.com',
            'password': 'password123'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])

    def test_api_auth_logout(self):
        """Test logout route."""
        self.login()

        response = self.client.post('/api/auth/logout')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

        # Verify session is cleared
        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)
            self.assertNotIn('username', session)

    def test_api_projects_get_unauthorized(self):
        """Test getting projects without authentication."""
        response = self.client.get('/api/projects')
        data = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])

    def test_api_projects_get(self):
        """Test getting projects."""
        self.login()

        response = self.client.get('/api/projects')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['projects']), 1)
        self.assertEqual(data['projects'][0]['name'], 'Test Project')

    def test_api_projects_create(self):
        """Test creating a project."""
        self.login()

        response = self.client.post('/api/projects', json={
            'name': 'New Project',
            'description': 'This is a new project'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['name'], 'New Project')
        self.assertEqual(data['project']['description'], 'This is a new project')

        # Verify project was created in database
        project = Project.query.filter_by(name='New Project').first()
        self.assertIsNotNone(project)
        self.assertEqual(project.description, 'This is a new project')
        self.assertEqual(project.user_id, self.test_user.id)

    def test_api_projects_get_single(self):
        """Test getting a single project."""
        self.login()

        response = self.client.get(f'/api/projects/{self.test_project.id}')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['name'], 'Test Project')
        self.assertEqual(len(data['project']['files']), 1)
        self.assertEqual(data['project']['files'][0]['filename'], 'test_file.txt')

    def test_api_projects_update(self):
        """Test updating a project."""
        self.login()

        response = self.client.put(f'/api/projects/{self.test_project.id}', json={
            'name': 'Updated Project',
            'description': 'This project has been updated'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['name'], 'Updated Project')
        self.assertEqual(data['project']['description'], 'This project has been updated')

        # Verify project was updated in database
        project = Project.query.get(self.test_project.id)
        self.assertEqual(project.name, 'Updated Project')
        self.assertEqual(project.description, 'This project has been updated')

    def test_api_projects_delete(self):
        """Test deleting a project."""
        self.login()

        response = self.client.delete(f'/api/projects/{self.test_project.id}')

        self.assertEqual(response.status_code, 200)

        # Verify project was deleted from database
        project = Project.query.get(self.test_project.id)
        self.assertIsNone(project)

        # Verify associated files were deleted
        file = File.query.get(self.test_file.id)
        self.assertIsNone(file)

    def test_api_files_get(self):
        """Test getting files for a project."""
        self.login()

        response = self.client.get(f'/api/projects/{self.test_project.id}/files')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['files']), 1)
        self.assertEqual(data['files'][0]['filename'], 'test_file.txt')
        self.assertEqual(data['files'][0]['file_type'], 'text')

    def test_api_files_create_text(self):
        """Test creating a text file."""
        self.login()

        response = self.client.post(f'/api/projects/{self.test_project.id}/files', data={
            'filename': 'new_text_file.txt',
            'content': 'This is new text file content'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['filename'], 'new_text_file.txt')
        self.assertEqual(data['file']['file_type'], 'text')

        # Verify file was created in database
        file = File.query.filter_by(filename='new_text_file.txt').first()
        self.assertIsNotNone(file)
        self.assertEqual(file.content, 'This is new text file content')
        self.assertEqual(file.project_id, self.test_project.id)

        # Verify file version was created
        version = FileVersion.query.filter_by(file_id=file.id).first()
        self.assertIsNotNone(version)
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.content, 'This is new text file content')

    def test_api_files_upload(self):
        """Test uploading a file."""
        self.login()

        # Create a test file for upload
        data = {}
        data['file'] = (io.BytesIO(b'Test file content for upload'), 'uploaded_file.txt')

        response = self.client.post(
            f'/api/projects/{self.test_project.id}/files',
            data=data,
            content_type='multipart/form-data'
        )
        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(result['success'])
        self.assertEqual(result['file']['filename'], 'uploaded_file.txt')

        # Verify file was created in database
        file = File.query.filter_by(filename='uploaded_file.txt').first()
        self.assertIsNotNone(file)
        self.assertEqual(file.project_id, self.test_project.id)

        # Verify physical file was created
        self.assertTrue(os.path.exists(file.file_path))

    def test_api_files_get_single(self):
        """Test getting a single file."""
        self.login()

        response = self.client.get(f'/api/files/{self.test_file.id}')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['filename'], 'test_file.txt')
        self.assertEqual(data['file']['content'], 'This is test content')
        self.assertEqual(len(data['file']['versions']), 1)

    def test_api_files_update(self):
        """Test updating a file."""
        self.login()

        response = self.client.put(f'/api/files/{self.test_file.id}', json={
            'content': 'Updated file content',
            'commit_message': 'Update test file'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['content'], 'Updated file content')

        # Verify file was updated in database
        file = File.query.get(self.test_file.id)
        self.assertEqual(file.content, 'Updated file content')

        # Verify new version was created
        versions = FileVersion.query.filter_by(file_id=self.test_file.id).order_by(FileVersion.version_number).all()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[1].version_number, 2)
        self.assertEqual(versions[1].content, 'Updated file content')
        self.assertEqual(versions[1].commit_message, 'Update test file')

    def test_api_files_delete(self):
        """Test deleting a file."""
        self.login()

        response = self.client.delete(f'/api/files/{self.test_file.id}')

        self.assertEqual(response.status_code, 200)

        # Verify file was deleted from database
        file = File.query.get(self.test_file.id)
        self.assertIsNone(file)

        # Verify versions were deleted
        versions = FileVersion.query.filter_by(file_id=self.test_file.id).all()
        self.assertEqual(len(versions), 0)

    def test_api_file_versions(self):
        """Test getting file version."""
        self.login()

        response = self.client.get(f'/api/files/{self.test_file.id}/versions/{self.test_version.id}')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['version']['version_number'], 1)
        self.assertEqual(data['version']['content'], 'This is test content')
        self.assertEqual(data['version']['commit_message'], 'Initial commit')

    @patch('app.utils.enhance_image_with_stable_diffusion')
    def test_api_files_enhance(self, mock_enhance):
        """Test enhancing an image file."""
        self.login()

        # Create a test image file
        image_path = os.path.join(TestConfig.UPLOAD_FOLDER, 'test_image.jpg')
        with open(image_path, 'wb') as f:
            f.write(b'fake image data')

        image_file = File(
            filename='test_image.jpg',
            file_path=image_path,
            file_type='image',
            project_id=self.test_project.id
        )
        db.session.add(image_file)
        db.session.commit()

        # Mock enhancement function
        mock_enhance.return_value = True

        # Create enhanced image file
        enhanced_path = os.path.join(TestConfig.UPLOAD_FOLDER, 'test_image_enhanced.jpg')
        with open(enhanced_path, 'wb') as f:
            f.write(b'fake enhanced image data')

        response = self.client.post(f'/api/files/{image_file.id}/enhance', json={
            'type': 'stable_diffusion'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue('enhanced' in data['file']['filename'])

        # Verify mock was called
        mock_enhance.assert_called_once()

    @patch('app.github_integration.GitHubIntegration.verify_ssh_setup')
    def test_api_github_verify_ssh(self, mock_verify):
        """Test GitHub SSH verification."""
        self.login()

        # Mock SSH verification
        mock_verify.return_value = {'success': True}

        response = self.client.get('/api/github/verify-ssh')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

        # Test failed verification
        mock_verify.return_value = {'success': False, 'error': 'SSH key not found'}

        response = self.client.get('/api/github/verify-ssh')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'SSH key not found')

    @patch('app.github_integration.GitHubIntegration.verify_ssh_setup')
    @patch('app.github_integration.GitHubIntegration.publish_project_to_github')
    def test_api_github_publish(self, mock_publish, mock_verify):
        """Test publishing to GitHub."""
        self.login()

        # Mock SSH verification and publish
        mock_verify.return_value = {'success': True}
        mock_publish.return_value = {
            'success': True,
            'repo_name': 'eln-test-project',
            'full_name': 'test_user/eln-test-project',
            'html_url': 'https://github.com/test_user/eln-test-project',
            'ssh_url': 'git@github.com:test_user/eln-test-project.git'
        }

        response = self.client.post(f'/api/projects/{self.test_project.id}/github/publish')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['github']['repo_name'], 'eln-test-project')
        self.assertEqual(data['github']['full_name'], 'test_user/eln-test-project')

        # Verify project was updated
        project = Project.query.get(self.test_project.id)
        self.assertEqual(project.github_repo, 'test_user/eln-test-project')

        # Test failing SSH verification
        mock_verify.return_value = {'success': False, 'error': 'SSH key not found'}

        response = self.client.post(f'/api/projects/{self.test_project.id}/github/publish')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertTrue(data['ssh_error'])

    @patch('app.github_integration.GitHubIntegration.verify_ssh_setup')
    @patch('app.github_integration.GitHubIntegration.import_project_from_github')
    def test_api_github_import(self, mock_import, mock_verify):
        """Test importing from GitHub."""
        self.login()

        # Mock SSH verification and import
        mock_verify.return_value = {'success': True}

        # Create a mock project
        mock_project = MagicMock()
        mock_project.id = 999
        mock_project.name = 'Imported Project'
        mock_project.description = 'Imported from GitHub'
        mock_project.created_at = '2023-01-01T00:00:00'
        mock_project.updated_at = '2023-01-01T00:00:00'
        mock_project.github_repo = 'test_user/imported-project'

        mock_import.return_value = {
            'success': True,
            'project': mock_project,
            'repo': {
                'name': 'imported-project',
                'full_name': 'test_user/imported-project',
                'html_url': 'https://github.com/test_user/imported-project',
                'ssh_url': 'git@github.com:test_user/imported-project.git'
            }
        }

        response = self.client.post('/api/github/import', json={
            'repo_url': 'test_user/imported-project'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['name'], 'Imported Project')
        self.assertEqual(data['project']['github_repo'], 'test_user/imported-project')

        # Test failing SSH verification
        mock_verify.return_value = {'success': False, 'error': 'SSH key not found'}

        response = self.client.post('/api/github/import', json={
            'repo_url': 'test_user/imported-project'
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertTrue(data['ssh_error'])

    @patch('app.latex_export.LatexExport.export_project_to_pdf')
    def test_api_export_pdf(self, mock_export):
        """Test exporting to PDF."""
        self.login()

        # Mock PDF export
        mock_export.return_value = {
            'success': True,
            'pdf_content': b'Fake PDF content'
        }

        response = self.client.get(f'/api/projects/{self.test_project.id}/export/pdf')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertEqual(response.headers['Content-Disposition'], f'attachment; filename={self.test_project.name}.pdf')

        # Test export failure
        mock_export.return_value = {
            'success': False,
            'error': 'PDF generation failed'
        }

        response = self.client.get(f'/api/projects/{self.test_project.id}/export/pdf')
        data = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'PDF generation failed')

    @patch('app.ollama_integration.OllamaIntegration.search_projects')
    def test_api_search(self, mock_search):
        """Test project search."""
        self.login()

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
                                'id': self.test_file.id,
                                'filename': 'test_file.txt',
                                'file_type': 'text'
                            }
                        ]
                    },
                    'relevance_score': 8.5
                }
            ]
        }

        response = self.client.get('/api/search?q=test')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['project']['name'], 'Test Project')
        self.assertAlmostEqual(data['results'][0]['relevance_score'], 8.5)

        # Test empty query
        response = self.client.get('/api/search')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])

        # Test search failure
        mock_search.return_value = {
            'success': False,
            'error': 'Search failed'
        }

        response = self.client.get('/api/search?q=test')
        data = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertFalse(data['success'])

    def test_error_handling(self):
        """Test error handling in routes."""
        self.login()

        # Test 404 for non-existent project
        response = self.client.get('/api/projects/999')
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Project not found')

        # Test 404 for non-existent file
        response = self.client.get('/api/files/999')
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'File not found')

        # Test 400 for invalid request
        response = self.client.post('/api/projects', json={})
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])

    def test_authentication_required(self):
        """Test that routes require authentication."""
        # Test projects routes
        routes = [
            ('/api/projects', 'GET'),
            ('/api/projects', 'POST'),
            (f'/api/projects/{self.test_project.id}', 'GET'),
            (f'/api/projects/{self.test_project.id}', 'PUT'),
            (f'/api/projects/{self.test_project.id}', 'DELETE'),
            (f'/api/projects/{self.test_project.id}/files', 'GET'),
            (f'/api/projects/{self.test_project.id}/files', 'POST'),
            (f'/api/files/{self.test_file.id}', 'GET'),
            (f'/api/files/{self.test_file.id}', 'PUT'),
            (f'/api/files/{self.test_file.id}', 'DELETE'),
            (f'/api/projects/{self.test_project.id}/github/publish', 'POST'),
            ('/api/github/import', 'POST'),
            ('/api/search', 'GET'),
        ]

        for route, method in routes:
            if method == 'GET':
                response = self.client.get(route)
            elif method == 'POST':
                response = self.client.post(route, json={})
            elif method == 'PUT':
                response = self.client.put(route, json={})
            elif method == 'DELETE':
                response = self.client.delete(route)

            data = response.get_json()
            self.assertEqual(response.status_code, 401, f"Route {method} {route} should require authentication")
            self.assertFalse(data['success'])
            self.assertEqual(data['message'], 'Not logged in')


if __name__ == '__main__':
    unittest.main()
