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
import hashlib
import datetime
from datetime import datetime
import io
import re
from .rtf_handler import is_rtf_content, extract_text_from_rtf, process_rtf_file, handle_content_update
from .digital_signature import DigitalSignature

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

# Initialize signature manager
def get_signature_manager():
    return DigitalSignature()

@main_bp.route('/api/create-signature', methods=['POST'])
def create_signature():
    """Create a digital signature for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    username = session.get('username', 'Unknown User')
    user_id = session.get('user_id')
    
    # Create timestamp and signature
    sig_manager = get_signature_manager()
    timestamp = sig_manager.create_timestamp()
    
    # Add additional context for the signature
    additional_data = data.get('additional_data', {})
    if isinstance(additional_data, str):
        additional_data = {'context': additional_data}
    
    # Add user ID for verification
    additional_data['user_id'] = user_id
    
    # Create the signature
    signature = sig_manager.create_signature(username, timestamp, additional_data)
    
    # Return both the signature data and a formatted display version
    return jsonify({
        'success': True,
        'signature': signature,
        'formatted': sig_manager.format_signature_for_display(signature)
    })

@main_bp.route('/api/verify-signature', methods=['POST'])
def verify_signature():
    """Verify a digital signature"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    signature_data = data.get('signature')
    signature_b64 = signature_data.get('signature')
    
    # Create the original data JSON string
    original_data = {
        'username': signature_data.get('username'),
        'timestamp': signature_data.get('timestamp'),
        'data': signature_data.get('data')
    }
    original_json = json.dumps(original_data, sort_keys=True)
    
    # Verify the signature
    sig_manager = get_signature_manager()
    is_valid = sig_manager.verify_signature(original_json, signature_b64)
    
    return jsonify({
        'success': True,
        'valid': is_valid,
        'message': 'Signature is valid' if is_valid else 'Signature verification failed'
    })

@main_bp.route('/api/file/<int:file_id>/add-signature', methods=['POST'])
def add_file_signature(file_id):
    """Add a digital signature to a file and save it"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    file = File.query.join(Project).filter(File.id == file_id, Project.user_id == user_id).first()
    
    if not file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Only allow signing text files
    if file.file_type != 'text':
        return jsonify({'success': False, 'message': 'Only text files can be signed'}), 400
    
    data = request.get_json()
    username = session.get('username', 'Unknown User')
    
    # Create timestamp and signature
    sig_manager = get_signature_manager()
    timestamp = sig_manager.create_timestamp()
    
    # Add file context to the signature
    additional_data = {
        'file_id': file.id,
        'filename': file.filename,
        'content_hash': hashlib.sha256(file.content.encode('utf-8')).hexdigest()
    }
    
    # Create the signature
    signature = sig_manager.create_signature(username, timestamp, additional_data)
    
    # Format the signature for insertion
    formatted_signature = sig_manager.format_signature_for_display(signature)
    
    # Determine where to add the signature
    position = data.get('position', 'end')  # 'end', 'start', or 'cursor'
    if position == 'end':
        # Add signature at the end of the content
        file.content = file.content + "\n\n" + formatted_signature
    elif position == 'start':
        # Add signature at the beginning of the content
        file.content = formatted_signature + "\n\n" + file.content
    else:
        # If position is not specified or invalid, add at the end
        file.content = file.content + "\n\n" + formatted_signature
    
    # Update file
    file.updated_at = datetime.utcnow()
    
    # Create a new version
    last_version = FileVersion.query.filter_by(file_id=file.id).order_by(FileVersion.version_number.desc()).first()
    version_number = 1
    if last_version:
        version_number = last_version.version_number + 1
    
    version = FileVersion(
        version_number=version_number,
        content=file.content,
        file_path=file.file_path,
        commit_message=f"Added digital signature by {username}",
        file_id=file.id
    )
    
    db.session.add(version)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Signature added to file',
        'file': {
            'id': file.id,
            'filename': file.filename,
            'content': file.content
        },
        'signature': signature
    })

# Route for home page
@main_bp.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@main_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset a user's password without email verification (for testing purposes)"""
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    if not username or not new_password:
        return jsonify({'success': False, 'message': 'Username and new password are required'}), 400
    
    # Find the user
    user = User.query.filter_by(username=username).first()
    
    if not user:
        # Return success even if user doesn't exist for security reasons
        # This prevents username enumeration attacks
        return jsonify({'success': True, 'message': 'If the username exists, the password has been reset'})
    
    # Update the password
    user.password_hash = hash_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'If the username exists, the password has been reset'})

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
        project_data = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'file_count': project.files.count(),
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

        projects_list.append(project_data)

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
        
        # Check if content is RTF
        rtf_content = None
        if content.strip().startswith('{\\rtf'):
            print(f"RTF content detected in {filename}, storing both RTF and plain text")
            rtf_content = content
            
            # Extract plain text from RTF for display and search
            try:
                # Simple RTF to text conversion - strip RTF tags
                cleaned_content = re.sub(r'\\[a-z0-9]+', ' ', content)  # Remove control words
                cleaned_content = re.sub(r'\{|\}', '', cleaned_content)  # Remove braces
                cleaned_content = re.sub(r'\\\'[0-9a-f]{2}', '', cleaned_content)  # Remove hex escapes
                cleaned_content = re.sub(r'\\par', '\n', cleaned_content)  # Replace paragraph marks with newlines
                cleaned_content = re.sub(r'\\\*.*?;', '', cleaned_content)  # Remove other control sequences
                
                # Further clean up whitespace
                cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
                
                content = cleaned_content.strip()
                print(f"Extracted plain text: {len(content)} characters")
            except Exception as rtf_err:
                print(f"Error processing RTF content: {rtf_err}")
                # Keep the original content if extraction fails
        
        # Create file record with RTF support
        file = File(
            filename=filename,
            file_path=os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            file_type='text',
            content=content,
            rtf_content=rtf_content,  # Store the RTF content if available
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
        
        # Create initial version with RTF support
        version = FileVersion(
            version_number=1,
            content=content,
            rtf_content=rtf_content,  # Store the RTF content in the version as well
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
                'updated_at': file.updated_at.isoformat(),
                'has_rtf': rtf_content is not None  # Indicate if the file has RTF content
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
        rtf_content = None
        
        if original_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            file_type = 'image'
        elif original_filename.lower().endswith('.rtf'):
            file_type = 'text'
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    rtf_content = f.read()
                
                # Extract plain text from RTF for display and search
                try:
                    # Simple RTF to text conversion - strip RTF tags
                    cleaned_content = re.sub(r'\\[a-z0-9]+', ' ', rtf_content)
                    cleaned_content = re.sub(r'\{|\}', '', cleaned_content)
                    cleaned_content = re.sub(r'\\\'[0-9a-f]{2}', '', cleaned_content)
                    cleaned_content = re.sub(r'\\par', '\n', cleaned_content)
                    cleaned_content = re.sub(r'\\\*.*?;', '', cleaned_content)
                    
                    # Further clean up whitespace
                    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
                    
                    content = cleaned_content.strip()
                    print(f"Extracted plain text from RTF file: {len(content)} characters")
                except Exception as rtf_err:
                    print(f"Error processing RTF file: {rtf_err}")
                    content = "RTF content (could not extract plain text)"
            except Exception as e:
                print(f"Error reading RTF file: {str(e)}")
                file_type = 'binary'
        elif original_filename.lower().endswith(('.txt', '.md', '.csv', '.json')):
            file_type = 'text'
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check if the file contains RTF content despite the extension
                    if content.strip().startswith('{\\rtf'):
                        print(f"RTF content detected in {original_filename}")
                        rtf_content = content
                        
                        # Extract plain text from RTF
                        cleaned_content = re.sub(r'\\[a-z0-9]+', ' ', content)
                        cleaned_content = re.sub(r'\{|\}', '', cleaned_content)
                        cleaned_content = re.sub(r'\\\'[0-9a-f]{2}', '', cleaned_content)
                        cleaned_content = re.sub(r'\\par', '\n', cleaned_content)
                        cleaned_content = re.sub(r'\\\*.*?;', '', cleaned_content)
                        content = re.sub(r'\s+', ' ', cleaned_content).strip()
            except:
                # If reading as text fails, keep as binary
                file_type = 'binary'
        
        # Create file record with RTF support
        file = File(
            filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            content=content,
            rtf_content=rtf_content,  # Store the RTF content if available
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
        
        # Create initial version with RTF support
        version = FileVersion(
            version_number=1,
            content=content,
            rtf_content=rtf_content,  # Store the RTF content in the version as well
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
                'updated_at': file.updated_at.isoformat(),
                'has_rtf': rtf_content is not None  # Indicate if the file has RTF content
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
        response_data = {
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
        }
        
        # Add RTF content if available
        if hasattr(file, 'rtf_content') and file.rtf_content:
            response_data['file']['rtf_content'] = file.rtf_content
            response_data['file']['has_rtf'] = True
        
        return jsonify(response_data)
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
    
    # Get content and check for RTF
    new_content = data.get('content', file.content)
    new_rtf_content = data.get('rtf_content', None)
    
    # If no explicit RTF content was provided, check if the content is RTF
    if new_rtf_content is None and new_content.strip().startswith('{\\rtf'):
        print(f"RTF content detected in update for {file.filename}")
        new_rtf_content = new_content
        
        # Extract plain text from RTF for display and search
        try:
            # Simple RTF to text conversion - strip RTF tags
            cleaned_content = re.sub(r'\\[a-z0-9]+', ' ', new_content)  # Remove control words
            cleaned_content = re.sub(r'\{|\}', '', cleaned_content)  # Remove braces
            cleaned_content = re.sub(r'\\\'[0-9a-f]{2}', '', cleaned_content)  # Remove hex escapes
            cleaned_content = re.sub(r'\\par', '\n', cleaned_content)  # Replace paragraph marks with newlines
            cleaned_content = re.sub(r'\\\*.*?;', '', cleaned_content)  # Remove other control sequences
            
            # Further clean up whitespace
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
            
            new_content = cleaned_content.strip()
            print(f"Extracted plain text: {len(new_content)} characters")
        except Exception as rtf_err:
            print(f"Error processing RTF content: {rtf_err}")
            # Keep the original content if extraction fails
