from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app, session
from app.models import User, Project, File, FileVersion
from app import db
from app.utils import hash_password, verify_password, save_file
from app.neo4j_integration import Neo4jIntegration
from app.github_integration import GitHubIntegration
from app.ollama_integration import OllamaIntegration
from app.latex_export import LatexExport
import os
import json
from datetime import datetime
import io

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize integrations
def get_neo4j():
    return Neo4jIntegration()

def get_github():
    return GitHubIntegration()

def get_ollama():
    return OllamaIntegration()

def get_latex():
    return LatexExport()

# GitHub integration routes
@main_bp.route('/api/github/verify-ssh', methods=['GET'])
def verify_github_ssh():
    """Verify that SSH keys are set up correctly for GitHub"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    # Verify SSH keys
    github = get_github()
    result = github.verify_ssh_setup()
    
    return jsonify(result)

@main_bp.route('/api/projects/<int:project_id>/github/publish', methods=['POST'])
def publish_to_github(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Check SSH connection first
    github = get_github()
    ssh_result = github.verify_ssh_setup()
    
    if not ssh_result['success']:
        return jsonify({
            'success': False, 
            'message': 'GitHub SSH authentication is not set up correctly.',
            'error': ssh_result.get('error', 'Unknown SSH error'),
            'ssh_error': True
        }), 400
    
    # Get files
    files = File.query.filter_by(project_id=project.id).all()
    
    # Publish to GitHub
    result = github.publish_project_to_github(project, files)
    
    if not result['success']:
        return jsonify({
            'success': False, 
            'message': result.get('error', 'Failed to publish to GitHub')
        }), 500
    
    # Update project with GitHub repo info
    project.github_repo = result['full_name']
    db.session.commit()
    
    return jsonify({
        'success': True,
        'github': {
            'repo_name': result['repo_name'],
            'full_name': result['full_name'],
            'html_url': result['html_url'],
            'ssh_url': result.get('ssh_url', '')
        }
    })from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app, session
from app.models import User, Project, File, FileVersion
from app import db
from app.utils import hash_password, verify_password, save_file
from app.neo4j_integration import Neo4jIntegration
from app.github_integration import GitHubIntegration
from app.ollama_integration import OllamaIntegration
from app.latex_export import LatexExport
import os
import json
from datetime import datetime
import io

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize integrations
def get_neo4j():
    return Neo4jIntegration()

def get_github():
    return GitHubIntegration()

def get_ollama():
    return OllamaIntegration()

def get_latex():
    return LatexExport()

# Route for home page
@main_bp.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@main_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    # Create new user
    hashed_password = hash_password(data['password'])
    new_user = User(username=data['username'], email=data.get('email'), password_hash=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Add user to Neo4j
    try:
        neo4j = get_neo4j()
        neo4j.create_user_node(new_user.id, new_user.username)
    except Exception as e:
        # Log error but continue
        print(f"Neo4j error: {str(e)}")
    
    # Set session
    session['user_id'] = new_user.id
    session['username'] = new_user.username
    
    return jsonify({'success': True, 'user_id': new_user.id})

@main_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Find user
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not verify_password(user.password_hash, data['password']):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({'success': True, 'user_id': user.id})

@main_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    # Clear session
    session.pop('user_id', None)
    session.pop('username', None)
    
    return jsonify({'success': True})

# Check if user is logged in
@main_bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user_id': session['user_id'],
            'username': session['username']
        })
    
    return jsonify({'logged_in': False})

# Project routes
@main_bp.route('/api/projects', methods=['GET'])
def get_projects():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    projects = Project.query.filter_by(user_id=user_id).all()
    
    projects_list = []
    for project in projects:
        projects_list.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'file_count': project.files.count()
        })
    
    return jsonify({'success': True, 'projects': projects_list})

@main_bp.route('/api/projects', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Create project
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        user_id=user_id
    )
    
    db.session.add(project)
    db.session.commit()
    
    # Add project to Neo4j
    try:
        neo4j = get_neo4j()
        neo4j.create_project_node(project.id, project.name, project.description, user_id)
    except Exception as e:
        # Log error but continue
        print(f"Neo4j error: {str(e)}")
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }
    })

@main_bp.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Get files
    files = []
    for file in project.files:
        files.append({
            'id': file.id,
            'filename': file.filename,
            'file_type': file.file_type,
            'created_at': file.created_at.isoformat(),
            'updated_at': file.updated_at.isoformat()
        })
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'github_repo': project.github_repo,
            'files': files
        }
    })

@main_bp.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    data = request.get_json()
    
    # Update project
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }
    })

@main_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Delete associated files
    for file in project.files:
        # Delete physical file if it exists
        if os.path.exists(file.file_path):
            try:
                os.remove(file.file_path)
            except Exception as e:
                print(f"Error deleting file {file.file_path}: {str(e)}")
    
    # Delete project from database
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'success': True})

# File routes
@main_bp.route('/api/projects/<int:project_id>/files', methods=['GET'])
def get_files(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Get files
    files = []
    for file in project.files:
        files.append({
            'id': file.id,
            'filename': file.filename,
            'file_type': file.file_type,
            'created_at': file.created_at.isoformat(),
            'updated_at': file.updated_at.isoformat()
        })
    
    return jsonify({'success': True, 'files': files})

@main_bp.route('/api/projects/<int:project_id>/files', methods=['POST'])
def create_file(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Handle text file
    if 'content' in request.form:
        filename = request.form.get('filename', 'untitled.txt')
        content = request.form.get('content', '')
        
        # Create file record
        file = File(
            filename=filename,
            file_path=os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            file_type='text',
            content=content,
            project_id=project.id
        )
        
        db.session.add(file)
        db.session.commit()
        
        # Add to Neo4j
        try:
            neo4j = get_neo4j()
            neo4j.create_file_node(file.id, file.filename, file.file_type, content, project.id)
            
            # Extract keywords with Ollama
            ollama = get_ollama()
            keywords_result = ollama.extract_keywords(content)
            
            if keywords_result['success']:
                for keyword in keywords_result['keywords']:
                    neo4j.add_keyword_to_file(file.id, keyword)
        except Exception as e:
            # Log error but continue
            print(f"Integration error: {str(e)}")
        
        # Create initial version
        version = FileVersion(
            version_number=1,
            content=content,
            file_path=file.file_path,
            commit_message="Initial version",
            file_id=file.id
        )
        
        db.session.add(version)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file': {
                'id': file.id,
                'filename': file.filename,
                'file_type': file.file_type,
                'created_at': file.created_at.isoformat(),
                'updated_at': file.updated_at.isoformat()
            }
        })
    
    # Handle file upload
    elif 'file' in request.files:
        uploaded_file = request.files['file']
        
        if uploaded_file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Save file
        original_filename, safe_filename, file_path = save_file(uploaded_file, current_app.config['UPLOAD_FOLDER'])
        
        # Determine file type
        file_type = 'binary'
        content = None
        
        if original_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            file_type = 'image'
        elif original_filename.lower().endswith(('.txt', '.md', '.csv', '.json')):
            file_type = 'text'
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except:
                # If reading as text fails, keep as binary
                file_type = 'binary'
        
        # Create file record
        file = File(
            filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            content=content,
            project_id=project.id
        )
        
        db.session.add(file)
        db.session.commit()
        
        # Add to Neo4j
        try:
            neo4j = get_neo4j()
            neo4j.create_file_node(file.id, file.filename, file.file_type, content or "", project.id)
            
            # Extract keywords or analyze image with Ollama
            ollama = get_ollama()
            
            if file_type == 'text' and content:
                keywords_result = ollama.extract_keywords(content)
                
                if keywords_result['success']:
                    for keyword in keywords_result['keywords']:
                        neo4j.add_keyword_to_file(file.id, keyword)
            elif file_type == 'image':
                analysis_result = ollama.analyze_image(file_path)
                
                if analysis_result['success']:
                    # Extract keywords from the analysis
                    keywords_result = ollama.extract_keywords(analysis_result['analysis'])
                    
                    if keywords_result['success']:
                        for keyword in keywords_result['keywords']:
                            neo4j.add_keyword_to_file(file.id, keyword)
        except Exception as e:
            # Log error but continue
            print(f"Integration error: {str(e)}")
        
        # Create initial version
        version = FileVersion(
            version_number=1,
            content=content,
            file_path=file_path,
            commit_message="Initial version",
            file_id=file.id
        )
        
        db.session.add(version)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file': {
                'id': file.id,
                'filename': file.filename,
                'file_type': file.file_type,
                'created_at': file.created_at.isoformat(),
                'updated_at': file.updated_at.isoformat()
            }
        })
    
    else:
        return jsonify({'success': False, 'message': 'No file or content provided'}), 400

@main_bp.route('/api/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Get versions
    versions = []
    for version in file.versions:
        versions.append({
            'id': version.id,
            'version_number': version.version_number,
            'commit_message': version.commit_message,
            'created_at': version.created_at.isoformat()
        })
    
    # Return appropriate data based on file type
    if file.file_type == 'text':
        return jsonify({
            'success': True,
            'file': {
                'id': file.id,
                'filename': file.filename,
                'file_type': file.file_type,
                'content': file.content,
                'created_at': file.created_at.isoformat(),
                'updated_at': file.updated_at.isoformat(),
                'versions': versions
            }
        })
    else:
        # Return metadata for binary/image files
        return jsonify({
            'success': True,
            'file': {
                'id': file.id,
                'filename': file.filename,
                'file_type': file.file_type,
                'file_path': file.file_path,
                'created_at': file.created_at.isoformat(),
                'updated_at': file.updated_at.isoformat(),
                'versions': versions
            }
        })

@main_bp.route('/api/files/<int:file_id>/content', methods=['GET'])
def get_file_content(file_id):
    """Get the actual file content for binary/image files"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Send the file
    try:
        return send_file(file.file_path, download_name=file.filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/files/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    data = request.get_json()
    
    # Only allow updating text files
    if file.file_type != 'text':
        return jsonify({'success': False, 'message': 'Only text files can be updated'}), 400
    
    # Get commit message
    commit_message = data.get('commit_message', 'Updated file')
    
    # Update file content
    file.content = data.get('content', file.content)
    file.updated_at = datetime.utcnow()
    
    # Create new version
    last_version = FileVersion.query.filter_by(file_id=file.id).order_by(FileVersion.version_number.desc()).first()
    version_number = 1
    if last_version:
        version_number = last_version.version_number + 1
    
    version = FileVersion(
        version_number=version_number,
        content=file.content,
        file_path=file.file_path,
        commit_message=commit_message,
        file_id=file.id
    )
    
    db.session.add(version)
    db.session.commit()
    
    # Update Neo4j
    try:
        neo4j = get_neo4j()
        neo4j.create_file_node(file.id, file.filename, file.file_type, file.content, file.project_id)
        
        # Re-extract keywords with Ollama
        ollama = get_ollama()
        keywords_result = ollama.extract_keywords(file.content)
        
        if keywords_result['success']:
            for keyword in keywords_result['keywords']:
                neo4j.add_keyword_to_file(file.id, keyword)
    except Exception as e:
        # Log error but continue
        print(f"Integration error: {str(e)}")
    
    return jsonify({
        'success': True,
        'file': {
            'id': file.id,
            'filename': file.filename,
            'file_type': file.file_type,
            'content': file.content,
            'created_at': file.created_at.isoformat(),
            'updated_at': file.updated_at.isoformat(),
            'version': version_number
        }
    })

@main_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Delete physical file if it exists
    if os.path.exists(file.file_path):
        try:
            os.remove(file.file_path)
        except Exception as e:
            print(f"Error deleting file {file.file_path}: {str(e)}")
    
    # Delete file from database
    db.session.delete(file)
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/api/files/<int:file_id>/versions/<int:version_id>', methods=['GET'])
def get_file_version(file_id, version_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    version = FileVersion.query.filter_by(id=version_id, file_id=file.id).first()
    
    if not version:
        return jsonify({'success': False, 'message': 'Version not found'}), 404
    
    return jsonify({
        'success': True,
        'version': {
            'id': version.id,
            'version_number': version.version_number,
            'content': version.content,
            'commit_message': version.commit_message,
            'created_at': version.created_at.isoformat()
        }
    })

# Image enhancement routes
@main_bp.route('/api/files/<int:file_id>/enhance', methods=['POST'])
def enhance_image(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Check if file is an image
    if file.file_type != 'image':
        return jsonify({'success': False, 'message': 'File is not an image'}), 400
    
    data = request.get_json()
    enhancement_type = data.get('type', 'stable_diffusion')
    
    # Generate enhanced filename
    name, ext = os.path.splitext(file.filename)
    enhanced_filename = f"{name}_enhanced{ext}"
    enhanced_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], enhanced_filename)
    
    # Apply enhancement
    if enhancement_type == 'stable_diffusion':
        from app.utils import enhance_image_with_stable_diffusion
        success = enhance_image_with_stable_diffusion(file.file_path, enhanced_file_path)
    elif enhancement_type == 'ollama':
        ollama = get_ollama()
        result = ollama.enhance_image_to_line_art(file.file_path, enhanced_file_path)
        success = result['success']
    else:
        return jsonify({'success': False, 'message': 'Invalid enhancement type'}), 400
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to enhance image'}), 500
    
    # Create new file for enhanced image
    enhanced_file = File(
        filename=enhanced_filename,
        file_path=enhanced_file_path,
        file_type='image',
        project_id=file.project_id
    )
    
    db.session.add(enhanced_file)
    db.session.commit()
    
    # Add to Neo4j
    try:
        neo4j = get_neo4j()
        neo4j.create_file_node(enhanced_file.id, enhanced_file.filename, enhanced_file.file_type, "", file.project_id)
        
        # Connect the original and enhanced images
        # Add a relationship in Neo4j
    except Exception as e:
        # Log error but continue
        print(f"Neo4j error: {str(e)}")
    
    return jsonify({
        'success': True,
        'file': {
            'id': enhanced_file.id,
            'filename': enhanced_file.filename,
            'file_type': enhanced_file.file_type,
            'created_at': enhanced_file.created_at.isoformat(),
            'updated_at': enhanced_file.updated_at.isoformat()
        }
    })

# GitHub integration routes
@main_bp.route('/api/projects/<int:project_id>/github/publish', methods=['POST'])
def publish_to_github(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Get files
    files = File.query.filter_by(project_id=project.id).all()
    
    # Publish to GitHub
    github = get_github()
    result = github.publish_project_to_github(project, files)
    
    if not result['success']:
        return jsonify({'success': False, 'message': result.get('error', 'Failed to publish to GitHub')}), 500
    
    # Update project with GitHub repo info
    project.github_repo = result['full_name']
    db.session.commit()
    
    return jsonify({
        'success': True,
        'github': {
            'repo_name': result['repo_name'],
            'full_name': result['full_name'],
            'html_url': result['html_url']
        }
    })

@main_bp.route('/api/github/import', methods=['POST'])
def import_from_github():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({'success': False, 'message': 'Repository URL or name is required'}), 400
    
    # Check SSH connection first
    github = get_github()
    ssh_result = github.verify_ssh_setup()
    
    if not ssh_result['success']:
        return jsonify({
            'success': False, 
            'message': 'GitHub SSH authentication is not set up correctly.',
            'error': ssh_result.get('error', 'Unknown SSH error'),
            'ssh_error': True
        }), 400
    
    # Import from GitHub
    result = github.import_project_from_github(repo_url, user_id)
    
    if not result['success']:
        return jsonify({'success': False, 'message': result.get('error', 'Failed to import from GitHub')}), 500
    
    project = result['project']
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'github_repo': project.github_repo
        },
        'repo': result.get('repo', {})
    })

# LaTeX export route
@main_bp.route('/api/projects/<int:project_id>/export/pdf', methods=['GET'])
def export_to_pdf(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Get files
    files = File.query.filter_by(project_id=project.id).all()
    
    # Export to PDF
    latex = get_latex()
    result = latex.export_project_to_pdf(project, files)
    
    if not result['success']:
        return jsonify({'success': False, 'message': result.get('error', 'Failed to export to PDF')}), 500
    
    # Return PDF
    if 'pdf_path' in result:
        return send_file(result['pdf_path'], download_name=f"{project.name}.pdf")
    elif 'pdf_content' in result:
        return send_file(
            io.BytesIO(result['pdf_content']),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project.name}.pdf"
        )
    else:
        return jsonify({'success': False, 'message': 'PDF generation failed'}), 500

# Search routes
@main_bp.route('/api/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'success': False, 'message': 'Query is required'}), 400
    
    # Get projects for this user
    projects = Project.query.filter_by(user_id=user_id).all()
    
    # Prepare data for search
    projects_data = []
    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'files': []
        }
        
        # Add files
        for file in project.files:
            file_data = {
                'id': file.id,
                'filename': file.filename,
                'file_type': file.file_type
            }
            
            if file.file_type == 'text':
                file_data['content'] = file.content
            
            project_data['files'].append(file_data)
        
        projects_data.append(project_data)
    
    # Use Ollama for semantic search
    ollama = get_ollama()
    search_results = ollama.search_projects(query, projects_data)
    
    if not search_results['success']:
        return jsonify({'success': False, 'message': search_results.get('error', 'Search failed')}), 500
    
    # Extract Neo4j keywords for additional context
    try:
        keywords = query.split()
        neo4j = get_neo4j()
        related_files = neo4j.find_related_files(keywords)
        
        # Add relevance info from Neo4j
        for result in search_results['results']:
            for file_info in related_files:
                if str(result['project']['id']) == str(file_info['project_id']):
                    if 'neo4j_relevance' not in result:
                        result['neo4j_relevance'] = []
                    result['neo4j_relevance'].append({
                        'file_id': file_info['file_id'],
                        'filename': file_info['filename'],
                        'relevance': file_info['relevance']
                    })
    except Exception as e:
        # Log error but continue
        print(f"Neo4j search error: {str(e)}")
    
    return jsonify({
        'success': True,
        'results': search_results['results']
    })
