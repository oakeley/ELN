import unittest
import os
import tempfile
from datetime import datetime

from app import create_app, db
from app.models import User, Project, File, FileVersion
from config import Config

class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = tempfile.mkdtemp()


class TestDatabaseModels(unittest.TestCase):
    """Test cases for database models."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user
        self.test_user = User(username='testuser', email='test@example.com', password_hash='hashed_password')
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_model(self):
        """Test User model functionality."""
        # Test user creation
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.password_hash, 'hashed_password')

        # Test user representation
        self.assertEqual(str(user), '<User testuser>')

    def test_project_model(self):
        """Test Project model functionality."""
        # Create a project
        project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Test project retrieval
        retrieved_project = Project.query.filter_by(name='Test Project').first()
        self.assertIsNotNone(retrieved_project)
        self.assertEqual(retrieved_project.name, 'Test Project')
        self.assertEqual(retrieved_project.description, 'This is a test project')
        self.assertEqual(retrieved_project.user_id, self.test_user.id)

        # Test project-user relationship
        user = User.query.get(self.test_user.id)
        self.assertIn(project, user.projects)

        # Test timestamps
        self.assertIsInstance(project.created_at, datetime)
        self.assertIsInstance(project.updated_at, datetime)

        # Test project representation
        self.assertEqual(str(project), '<Project Test Project>')

    def test_file_model(self):
        """Test File model functionality."""
        # Create a project
        project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Create a file
        file = File(
            filename='test_file.txt',
            file_path='/path/to/test_file.txt',
            file_type='text',
            content='This is test content',
            project_id=project.id
        )
        db.session.add(file)
        db.session.commit()

        # Test file retrieval
        retrieved_file = File.query.filter_by(filename='test_file.txt').first()
        self.assertIsNotNone(retrieved_file)
        self.assertEqual(retrieved_file.filename, 'test_file.txt')
        self.assertEqual(retrieved_file.file_path, '/path/to/test_file.txt')
        self.assertEqual(retrieved_file.file_type, 'text')
        self.assertEqual(retrieved_file.content, 'This is test content')
        self.assertEqual(retrieved_file.project_id, project.id)

        # Test file-project relationship
        project = Project.query.get(project.id)
        self.assertIn(file, project.files)

        # Test timestamps
        self.assertIsInstance(file.created_at, datetime)
        self.assertIsInstance(file.updated_at, datetime)

        # Test file representation
        self.assertEqual(str(file), '<File test_file.txt>')

    def test_file_version_model(self):
        """Test FileVersion model functionality."""
        # Create a project
        project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Create a file
        file = File(
            filename='test_file.txt',
            file_path='/path/to/test_file.txt',
            file_type='text',
            content='This is test content',
            project_id=project.id
        )
        db.session.add(file)
        db.session.commit()

        # Create a file version
        version = FileVersion(
            version_number=1,
            content='This is the initial version',
            file_path='/path/to/test_file.txt',
            commit_message='Initial commit',
            file_id=file.id
        )
        db.session.add(version)
        db.session.commit()

        # Test version retrieval
        retrieved_version = FileVersion.query.filter_by(file_id=file.id).first()
        self.assertIsNotNone(retrieved_version)
        self.assertEqual(retrieved_version.version_number, 1)
        self.assertEqual(retrieved_version.content, 'This is the initial version')
        self.assertEqual(retrieved_version.file_path, '/path/to/test_file.txt')
        self.assertEqual(retrieved_version.commit_message, 'Initial commit')
        self.assertEqual(retrieved_version.file_id, file.id)

        # Test version-file relationship
        file = File.query.get(file.id)
        self.assertIn(version, file.versions)

        # Test timestamp
        self.assertIsInstance(version.created_at, datetime)

        # Test version representation
        self.assertEqual(str(version), f'<FileVersion {file.id}:1>')

    def test_cascade_delete(self):
        """Test cascade delete functionality."""
        # Create a project
        project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Create a file
        file = File(
            filename='test_file.txt',
            file_path='/path/to/test_file.txt',
            file_type='text',
            content='This is test content',
            project_id=project.id
        )
        db.session.add(file)
        db.session.commit()

        # Create a file version
        version = FileVersion(
            version_number=1,
            content='This is the initial version',
            file_path='/path/to/test_file.txt',
            commit_message='Initial commit',
            file_id=file.id
        )
        db.session.add(version)
        db.session.commit()

        # Delete project and check if file and version are also deleted
        db.session.delete(project)
        db.session.commit()

        self.assertIsNone(Project.query.get(project.id))
        self.assertIsNone(File.query.get(file.id))
        self.assertIsNone(FileVersion.query.get(version.id))

    def test_file_type_validation(self):
        """Test file type validation."""
        # Create a project
        project = Project(
            name='Test Project',
            description='This is a test project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Test valid file types
        valid_types = ['text', 'image', 'binary']
        for file_type in valid_types:
            file = File(
                filename=f'test_file_{file_type}.txt',
                file_path=f'/path/to/test_file_{file_type}.txt',
                file_type=file_type,
                project_id=project.id
            )
            db.session.add(file)
            try:
                db.session.commit()
                self.assertTrue(True)  # No exception raised
            except:
                self.fail(f"File type '{file_type}' should be valid")

            # Clean up
            db.session.delete(file)
            db.session.commit()


if __name__ == '__main__':
    unittest.main()
