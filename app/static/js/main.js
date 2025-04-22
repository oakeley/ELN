// Main JavaScript for Electronic Laboratory Notebook

// Timestamp and Digital Signature functionality
document.addEventListener('DOMContentLoaded', function() {
    // Timestamp insertion
    const addTimestampBtn = document.getElementById('add-timestamp');
    if (addTimestampBtn) {
        addTimestampBtn.addEventListener('click', function() {
            const now = new Date();
            const formattedTime = now.toISOString().replace('T', ' ').slice(0, 19);
            const timestampText = `[Timestamp: ${formattedTime}]`;
            
            // Insert at cursor position
            insertToActiveEditor(timestampText);
        });
    }
    
    // Digital signature insertion
    const addSignatureBtn = document.getElementById('add-signature');
    if (addSignatureBtn) {
        addSignatureBtn.addEventListener('click', function() {
            // First, create a secure digital signature from the server
            fetch('/api/create-signature', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    additional_data: 'Document signature requested from editor'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Insert the formatted signature
                    insertToActiveEditor(data.formatted);
                } else {
                    alert('Failed to create digital signature: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error creating signature:', error);
                
                // Fallback to a simple signature if the server request fails
                const username = document.getElementById('username-display')?.textContent || 'User';
                const now = new Date();
                const formattedTime = now.toISOString().replace('T', ' ').slice(0, 19);
                const signatureText = `[Signed: ${username} at ${formattedTime}]`;
                
                insertToActiveEditor(signatureText);
            });
        });
    }
    
    // Helper function to insert text into whichever editor is active
    function insertToActiveEditor(text) {
        const richTextContainer = document.getElementById('rich-text-container');
        const plainTextContainer = document.getElementById('plain-text-container');
        
        if (richTextContainer && plainTextContainer) {
            // Check which editor is active
            const isRichTextActive = !richTextContainer.classList.contains('d-none');
            
            if (isRichTextActive) {
                // Insert into rich text editor
                const editor = document.getElementById('rich-text-editor');
                insertHtmlAtCursor(editor, `<span class="eln-signature">${text}</span>`);
            } else {
                // Insert into plain text editor
                const textarea = document.getElementById('text-file-content');
                insertAtCursor(textarea, text);
            }
        } else {
            console.warn('Editor containers not found');
        }
    }
    
    // Helper function to insert text at cursor position in a textarea
    function insertAtCursor(field, text) {
        if (!field) return;
        
        if (field.selectionStart || field.selectionStart === 0) {
            const startPos = field.selectionStart;
            const endPos = field.selectionEnd;
            field.value = field.value.substring(0, startPos) 
                        + text 
                        + field.value.substring(endPos, field.value.length);
            field.selectionStart = startPos + text.length;
            field.selectionEnd = startPos + text.length;
            field.focus();
        } else {
            field.value += text;
        }
        
        // Trigger change event for any listeners
        field.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // Helper function to insert HTML at cursor position in a contenteditable div
    function insertHtmlAtCursor(element, html) {
        if (!element) return;
        
        // Focus the element if it's not already
        element.focus();
        
        // Get the current selection
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            // Get the first range of the selection
            const range = selection.getRangeAt(0);
            
            // Delete any current selection
            range.deleteContents();
            
            // Create a fragment with the HTML to insert
            const fragment = document.createRange().createContextualFragment(html);
            
            // Insert the fragment
            range.insertNode(fragment);
            
            // Move the caret to the end of the inserted content
            range.collapse(false);
            selection.removeAllRanges();
            selection.addRange(range);
        } else {
            // If no selection, just append to the end
            element.innerHTML += html;
        }
        
        // Trigger input event for any listeners
        element.dispatchEvent(new Event('input', { bubbles: true }));
    }
});

document.addEventListener('shown.bs.modal', function(event) {
    if (event.target.id === 'create-text-file-modal') {
        // Initialize the rich text editor
        const richTextToggle = document.querySelector('#toggle-editor');
        if (richTextToggle) {
            console.log('Modal opened, initializing rich text editor');
            
            // Ensure we start in plain text mode
            const richTextContainer = document.getElementById('rich-text-container');
            const plainTextContainer = document.getElementById('plain-text-container');
            
            if (richTextContainer) richTextContainer.classList.add('d-none');
            if (plainTextContainer) plainTextContainer.classList.remove('d-none');
            
            // Reset the button text
            richTextToggle.innerHTML = '<i class="fas fa-pen-fancy"></i> Rich Text';
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    console.log('Electronic Laboratory Notebook initialized');
    
    // Global state
    const state = {
        currentUser: null,
        currentProject: null,
        currentFile: null,
        projects: [],
        files: []
    };

    // UI Elements
    const ui = {
        // Sections
        authSection: document.getElementById('auth-section'),
        projectsSection: document.getElementById('projects-section'),
        projectDetailSection: document.getElementById('project-detail-section'),
        fileDetailSection: document.getElementById('file-detail-section'),
        searchSection: document.getElementById('search-section'),
        
        // Auth elements
        authButtons: document.getElementById('auth-buttons'),
        userInfo: document.getElementById('user-info'),
        usernameDisplay: document.getElementById('username-display'),
        loginButton: document.getElementById('login-button'),
        registerButton: document.getElementById('register-button'),
        logoutButton: document.getElementById('logout-button'),
        loginTab: document.getElementById('login-tab'),
        registerTab: document.getElementById('register-tab'),
        loginForm: document.getElementById('login-form'),
        registerForm: document.getElementById('register-form'),
        loginError: document.getElementById('login-error'),
        registerError: document.getElementById('register-error'),
        resetTab: document.getElementById('reset-tab'),
        resetForm: document.getElementById('reset-form'),
        resetError: document.getElementById('reset-error'),
        
        // Project elements
        projectsContainer: document.getElementById('projects-container'),
        createProjectButton: document.getElementById('create-project-button'),
        createProjectModal: new bootstrap.Modal(document.getElementById('create-project-modal')),
        createProjectForm: document.getElementById('create-project-form'),
        editProjectModal: new bootstrap.Modal(document.getElementById('edit-project-modal')),
        editProjectForm: document.getElementById('edit-project-form'),
        backToProjects: document.getElementById('back-to-projects'),
        projectDetailName: document.getElementById('project-detail-name'),
        projectDetailDescription: document.getElementById('project-detail-description'),
        editProject: document.getElementById('edit-project'),
        publishToGithub: document.getElementById('publish-to-github'),
        exportToPdf: document.getElementById('export-to-pdf'),
        deleteProject: document.getElementById('delete-project'),
        
        // File elements
        fileList: document.getElementById('file-list'),
        createTextFile: document.getElementById('create-text-file'),
        uploadFile: document.getElementById('upload-file'),
        createTextFileModal: new bootstrap.Modal(document.getElementById('create-text-file-modal')),
        createTextFileForm: document.getElementById('create-text-file-form'),
        uploadFileModal: new bootstrap.Modal(document.getElementById('upload-file-modal')),
        uploadFileForm: document.getElementById('upload-file-form'),
        backToProject: document.getElementById('back-to-project'),
        fileDetailName: document.getElementById('file-detail-name'),
        textFileView: document.getElementById('text-file-view'),
        imageFileView: document.getElementById('image-file-view'),
        fileContent: document.getElementById('file-content'),
        fileImage: document.getElementById('file-image'),
        fileLastUpdated: document.getElementById('file-last-updated'),
        fileVersions: document.getElementById('file-versions'),
        editFile: document.getElementById('edit-file'),
        enhanceImage: document.getElementById('enhance-image'),
        downloadFile: document.getElementById('download-file'),
        deleteFile: document.getElementById('delete-file'),
        editFileModal: new bootstrap.Modal(document.getElementById('edit-file-modal')),
        editFileForm: document.getElementById('edit-file-form'),
        enhanceImageModal: new bootstrap.Modal(document.getElementById('enhance-image-modal')),
        enhanceStableDiffusion: document.getElementById('enhance-stable-diffusion'),
        enhanceOllama: document.getElementById('enhance-ollama'),
        
        // Search elements
        navSearch: document.getElementById('nav-search'),
        searchInput: document.getElementById('search-input'),
        searchButton: document.getElementById('search-button'),
        searchResults: document.getElementById('search-results'),
        searchResultsList: document.getElementById('search-results-list'),
        noResultsMessage: document.getElementById('no-results-message'),
        
        // Navigation
        navProjects: document.getElementById('nav-projects')
    };

    // API functions
    const api = {
        // Auth
        async checkAuthStatus() {
            try {
                const response = await fetch('/api/auth/status');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error checking auth status:', error);
                return { logged_in: false };
            }
        },
        
        async login(username, password) {
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error logging in:', error);
                return { success: false, message: 'Network error' };
            }
        },
        
        async register(username, email, password) {
            console.log('API Register called with:', { username, email, password });
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                console.log('Register response:', data);
                return data;
            } catch (error) {
                console.error('Error registering:', error);
                return { success: false, message: 'Network error' };
            }
        },
        
        async logout() {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST'
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error logging out:', error);
                return { success: false };
            }
        },
        
        // Projects
        async getProjects() {
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching projects:', error);
                return { success: false, projects: [] };
            }
        },
        
        async createProject(name, description) {
            try {
                const response = await fetch('/api/projects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, description })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error creating project:', error);
                return { success: false };
            }
        },
        
        async getProject(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching project:', error);
                return { success: false };
            }
        },
        
        async updateProject(projectId, name, description) {
            try {
                const response = await fetch(`/api/projects/${projectId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, description })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error updating project:', error);
                return { success: false };
            }
        },
        
        async deleteProject(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    return { success: true };
                }
                
                return { success: false };
            } catch (error) {
                console.error('Error deleting project:', error);
                return { success: false };
            }
        },
        
        async publishToGithub(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/github/publish`, {
                    method: 'POST'
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error publishing to GitHub:', error);
                return { success: false };
            }
        },
        
        async exportToPdf(projectId) {
            try {
                window.open(`/api/projects/${projectId}/export/pdf`, '_blank');
                return { success: true };
            } catch (error) {
                console.error('Error exporting to PDF:', error);
                return { success: false };
            }
        },
        
        // Files
        async getFiles(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/files`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching files:', error);
                return { success: false, files: [] };
            }
        },
        
        async createTextFile(projectId, filename, content) {
            try {
                const formData = new FormData();
                formData.append('filename', filename);
                formData.append('content', content);
                
                const response = await fetch(`/api/projects/${projectId}/files`, {
                    method: 'POST',
                    body: formData
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error creating text file:', error);
                return { success: false };
            }
        },
        
        async uploadFile(projectId, file) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(`/api/projects/${projectId}/files`, {
                    method: 'POST',
                    body: formData
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error uploading file:', error);
                return { success: false };
            }
        },
        
        async getFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching file:', error);
                return { success: false };
            }
        },
        
        async updateFile(fileId, content, commitMessage) {
            try {
                const response = await fetch(`/api/files/${fileId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ content, commit_message: commitMessage })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error updating file:', error);
                return { success: false };
            }
        },
        
        async deleteFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    return { success: true };
                }
                
                return { success: false };
            } catch (error) {
                console.error('Error deleting file:', error);
                return { success: false };
            }
        },
        
        async enhanceImage(fileId, type) {
            try {
                const response = await fetch(`/api/files/${fileId}/enhance`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ type })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error enhancing image:', error);
                return { success: false };
            }
        },
        
        // Search
        async search(query) {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error searching:', error);
                return { success: false, results: [] };
            }
        },

        // GitHub SSH verification
        async verifyGithubSSH() {
            try {
                const response = await fetch('/api/github/verify-ssh');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error verifying GitHub SSH:', error);
                return { success: false, error: 'Network error' };
            }
        },

        // Reset Password
        async resetPassword(username, newPassword) {
            try {
                const response = await fetch('/api/auth/reset-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, new_password: newPassword })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error resetting password:', error);
                return { success: false, message: 'Network error' };
            }
        },

        // GitHub Import
        async importFromGithub(repoUrl) {
            try {
                const response = await fetch('/api/github/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ repo_url: repoUrl })
                });
                
                return await response.json();
            } catch (error) {
                console.error('Error importing from GitHub:', error);
                return { success: false, error: 'Network error' };
            }
        }
    };

    // UI handlers
    const handlers = {
        // Auth
        async handleLogin(e) {
            e.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            const result = await api.login(username, password);
            
            if (result.success) {
                state.currentUser = {
                    id: result.user_id,
                    username
                };
                ui.loginError.classList.add('d-none');
                ui.authSection.classList.add('d-none');
                ui.authButtons.classList.add('d-none');
                ui.userInfo.classList.remove('d-none');
                ui.usernameDisplay.textContent = username;
                
                // Show projects section
                ui.projectsSection.classList.remove('d-none');
                loadProjects();
            } else {
                ui.loginError.textContent = result.message || 'Login failed';
                ui.loginError.classList.remove('d-none');
            }
        },
        
        // Reset
        async handleResetPassword(e) {
            e.preventDefault();
            
            const username = document.getElementById('reset-username').value;
            const newPassword = document.getElementById('reset-new-password').value;
            const confirmPassword = document.getElementById('reset-confirm-password').value;
            
            // Basic validation
            if (!username || !newPassword) {
                ui.resetError.textContent = 'Username and new password are required';
                ui.resetError.classList.remove('d-none');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                ui.resetError.textContent = 'Passwords do not match';
                ui.resetError.classList.remove('d-none');
                return;
            }
            
            const result = await api.resetPassword(username, newPassword);
            
            if (result.success) {
                alert('Password has been reset. Please login with your new password.');
                ui.resetError.classList.add('d-none');
                ui.resetForm.reset();
                
                // Switch to login tab
                if (ui.loginTab) {
                    ui.loginTab.click();
                }
            } else {
                ui.resetError.textContent = result.message || 'Password reset failed';
                ui.resetError.classList.remove('d-none');
            }
        },

        async handleRegister(e) {
            e.preventDefault();
            console.log("Register form submitted");
            
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value || '';  // Make email optional
            const password = document.getElementById('register-password').value;
            
            // Add validation for username and password
            if (!username || !password) {
                ui.registerError.textContent = 'Username and password are required';
                ui.registerError.classList.remove('d-none');
                return;
            }
            
            console.log('Attempting to register:', { username, email, password: '********' });
            
            const result = await api.register(username, email, password);
            console.log('Registration result:', result);
            
            if (result.success) {
                state.currentUser = {
                    id: result.user_id,
                    username
                };
                ui.registerError.classList.add('d-none');
                ui.authSection.classList.add('d-none');
                ui.authButtons.classList.add('d-none');
                ui.userInfo.classList.remove('d-none');
                ui.usernameDisplay.textContent = username;
                
                // Show projects section
                ui.projectsSection.classList.remove('d-none');
                loadProjects();
            } else {
                ui.registerError.textContent = result.message || 'Registration failed';
                ui.registerError.classList.remove('d-none');
            }
        },
        
        async handleLogout() {
            const result = await api.logout();
            
            if (result.success) {
                state.currentUser = null;
                ui.userInfo.classList.add('d-none');
                ui.authButtons.classList.remove('d-none');
                ui.authSection.classList.remove('d-none');
                ui.projectsSection.classList.add('d-none');
                ui.projectDetailSection.classList.add('d-none');
                ui.fileDetailSection.classList.add('d-none');
                ui.searchSection.classList.add('d-none');
                
                // Reset forms
                ui.loginForm.reset();
                ui.registerForm.reset();
            }
        },
        
        // Projects
        async handleCreateProject(e) {
            e.preventDefault();
            
            const name = document.getElementById('project-name').value;
            const description = document.getElementById('project-description').value;
            
            const result = await api.createProject(name, description);
            
            if (result.success) {
                ui.createProjectModal.hide();
                ui.createProjectForm.reset();
                loadProjects();
            }
        },
        
        async handleEditProject(e) {
            e.preventDefault();
            
            const name = document.getElementById('edit-project-name').value;
            const description = document.getElementById('edit-project-description').value;
            
            const result = await api.updateProject(state.currentProject.id, name, description);
            
            if (result.success) {
                ui.editProjectModal.hide();
                loadProject(state.currentProject.id);
            }
        },
        
        async handleDeleteProject() {
            if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
                return;
            }
            
            const result = await api.deleteProject(state.currentProject.id);
            
            if (result.success) {
                ui.projectDetailSection.classList.add('d-none');
                ui.projectsSection.classList.remove('d-none');
                loadProjects();
            }
        },
        
        async handlePublishToGithub() {
            // First verify SSH authentication
            const sshCheck = await api.verifyGithubSSH();
            
            if (!sshCheck.success) {
                const errorMessage = 'GitHub SSH authentication is not properly configured.\n\n' +
                                    'Please make sure SSH keys are set up correctly.\n\n' +
                                    'Error: ' + (sshCheck.error || 'Unknown SSH error');
                alert(errorMessage);
                return;
            }
            
            const result = await api.publishToGithub(state.currentProject.id);
            
            if (result.success) {
                alert(`Project published to GitHub: ${result.github.html_url}`);
                loadProject(state.currentProject.id);
            } else if (result.ssh_error) {
                const errorMessage = 'GitHub SSH authentication failed.\n\n' +
                                    'Please verify your SSH keys are set up correctly and added to GitHub.\n' +
                                    'Error: ' + (result.error || 'Unknown SSH error');
                alert(errorMessage);
            } else {
                alert('Failed to publish to GitHub: ' + (result.message || 'Unknown error'));
            }
        },
        
        async handleExportToPdf() {
            await api.exportToPdf(state.currentProject.id);
        },
        
        async handleImportFromGithub() {
            const repoUrl = prompt('Enter GitHub repository URL or name:');
            if (!repoUrl) return;
            
            const result = await api.importFromGithub(repoUrl);
            
            if (result.success) {
                alert('GitHub repository imported successfully.');
                loadProjects();
            } else if (result.ssh_error) {
                alert('GitHub SSH authentication failed. Please verify your SSH keys are set up correctly.');
            } else {
                alert('Failed to import from GitHub: ' + (result.message || 'Unknown error'));
            }
        },
        
        // Files
        async handleCreateTextFile(e) {
            e.preventDefault();
            
            const filename = document.getElementById('text-file-name').value;
            const content = document.getElementById('text-file-content').value;
            
            const result = await api.createTextFile(state.currentProject.id, filename, content);
            
            if (result.success) {
                ui.createTextFileModal.hide();
                ui.createTextFileForm.reset();
                loadProject(state.currentProject.id);
            }
        },
        
        async handleUploadFile(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('file-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                return;
            }
            
            const result = await api.uploadFile(state.currentProject.id, file);
            
            if (result.success) {
                ui.uploadFileModal.hide();
                ui.uploadFileForm.reset();
                loadProject(state.currentProject.id);
            }
        },
        
        async handleEditFile(e) {
            e.preventDefault();
            
            const content = document.getElementById('edit-file-content').value;
            const commitMessage = document.getElementById('edit-file-commit').value;
            
            const result = await api.updateFile(state.currentFile.id, content, commitMessage);
            
            if (result.success) {
                ui.editFileModal.hide();
                loadFile(state.currentFile.id);
            }
        },
        
        async handleDeleteFile() {
            if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
                return;
            }
            
            const result = await api.deleteFile(state.currentFile.id);
            
            if (result.success) {
                ui.fileDetailSection.classList.add('d-none');
                ui.projectDetailSection.classList.remove('d-none');
                loadProject(state.currentProject.id);
            }
        },
        
        async handleEnhanceImage(type) {
            const result = await api.enhanceImage(state.currentFile.id, type);
            
            if (result.success) {
                ui.enhanceImageModal.hide();
                alert('Image enhancement complete. The enhanced image has been added to your project.');
                loadProject(state.currentProject.id);
            } else {
                alert('Failed to enhance image. Please try again.');
            }
        },
        
        // Search
        async handleSearch(e) {
            e.preventDefault();
            
            const query = ui.searchInput.value.trim();
            
            if (!query) {
                return;
            }
            
            const result = await api.search(query);
            
            if (result.success && result.results.length > 0) {
                ui.searchResults.classList.remove('d-none');
                ui.noResultsMessage.classList.add('d-none');
                renderSearchResults(result.results);
            } else {
                ui.searchResults.classList.add('d-none');
                ui.noResultsMessage.classList.remove('d-none');
            }
        }
    };

    // Rendering functions
    function renderProjects(projects) {
        ui.projectsContainer.innerHTML = '';
        
        if (projects.length === 0) {
            ui.projectsContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <p>You don't have any projects yet. Click "New Project" to get started.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        projects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'col-md-4 mb-4';
            card.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${project.name}</h5>
                        <p class="card-text text-muted">${project.description || 'No description'}</p>
                        <p><small class="text-muted">Files: ${project.file_count}</small></p>
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-outline-primary" data-project-id="${project.id}">Open</button>
                    </div>
                </div>
            `;
            
            // Add click handler
            const openButton = card.querySelector('button');
            openButton.addEventListener('click', () => {
                loadProject(project.id);
            });
            
            ui.projectsContainer.appendChild(card);
        });
    }
    
    function renderFiles(files) {
        ui.fileList.innerHTML = '';
        
        if (files.length === 0) {
            ui.fileList.innerHTML = `
                <div class="alert alert-info">
                    <p>This project doesn't have any files yet. Add a new text file or upload a file to get started.</p>
                </div>
            `;
            return;
        }
        
        files.forEach(file => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            item.href = '#';
            
            // Icon based on file type
            let icon = 'file-alt';
            if (file.file_type === 'image') {
                icon = 'file-image';
            } else if (file.file_type === 'binary') {
                icon = 'file-archive';
            }
            
            item.innerHTML = `
                <div>
                    <i class="fas fa-${icon} me-2"></i>
                    ${file.filename}
                </div>
                <small class="text-muted">Last updated: ${new Date(file.updated_at).toLocaleString()}</small>
            `;
            
            // Add click handler
            item.addEventListener('click', (e) => {
                e.preventDefault();
                loadFile(file.id);
            });
            
            ui.fileList.appendChild(item);
        });
    }
    
    function renderFileVersions(versions) {
        ui.fileVersions.innerHTML = '';
        
        if (versions.length === 0) {
            return;
        }
        
        versions.forEach(version => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            item.innerHTML = `
                <div>
                    <strong>Version ${version.version_number}</strong>
                    <p class="mb-0 text-muted">${version.commit_message || 'No commit message'}</p>
                </div>
                <small>${new Date(version.created_at).toLocaleString()}</small>
            `;
            
            ui.fileVersions.appendChild(item);
        });
    }
    
    function renderSearchResults(results) {
        ui.searchResultsList.innerHTML = '';
        
        results.forEach(result => {
            const project = result.project;
            const relevanceScore = result.relevance_score ? result.relevance_score.toFixed(1) : '?';
            
            const item = document.createElement('div');
            item.className = 'list-group-item';
            
            item.innerHTML = `
                <div class="d-flex justify-content-between">
                    <h5>${project.name}</h5>
                    <span class="badge bg-primary rounded-pill">Relevance: ${relevanceScore}/10</span>
                </div>
                <p>${project.description || 'No description'}</p>
                <button class="btn btn-sm btn-outline-primary" data-project-id="${project.id}">Open Project</button>
            `;
            
            // Add files if available
            if (project.files && project.files.length > 0) {
                const filesList = document.createElement('div');
                filesList.className = 'mt-2';
                filesList.innerHTML = '<h6>Relevant Files:</h6>';
                
                const filesUl = document.createElement('ul');
                filesUl.className = 'list-group list-group-flush mb-2';
                
                project.files.forEach(file => {
                    const fileItem = document.createElement('li');
                    fileItem.className = 'list-group-item py-1';
                    fileItem.innerHTML = `
                        <i class="fas fa-file-alt me-2"></i>
                        ${file.filename}
                    `;
                    filesUl.appendChild(fileItem);
                });
                
                filesList.appendChild(filesUl);
                item.appendChild(filesList);
            }
            
            // Add Neo4j relevance if available
            if (result.neo4j_relevance && result.neo4j_relevance.length > 0) {
                const relFilesList = document.createElement('div');
                relFilesList.className = 'mt-2';
                relFilesList.innerHTML = '<h6>Related Files:</h6>';
                
                const relFilesUl = document.createElement('ul');
                relFilesUl.className = 'list-group list-group-flush mb-2';
                
                result.neo4j_relevance.forEach(relFile => {
                    const fileItem = document.createElement('li');
                    fileItem.className = 'list-group-item py-1';
                    fileItem.innerHTML = `
                        <a href="#" class="file-link" data-file-id="${relFile.file_id}">
                            <i class="fas fa-file-alt me-2"></i>
                            ${relFile.filename}
                        </a>
                    `;
                    relFilesUl.appendChild(fileItem);
                });
                
                relFilesList.appendChild(relFilesUl);
                item.appendChild(relFilesList);
            }
            
            // Add open project handler
            const openButton = item.querySelector('button');
            openButton.addEventListener('click', () => {
                loadProject(project.id);
                ui.searchSection.classList.add('d-none');
                ui.projectDetailSection.classList.remove('d-none');
            });
            
            // Add file link handlers if available
            const fileLinks = item.querySelectorAll('.file-link');
            fileLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const fileId = link.getAttribute('data-file-id');
                    loadFile(fileId);
                    ui.searchSection.classList.add('d-none');
                    ui.fileDetailSection.classList.remove('d-none');
                });
            });
            
            ui.searchResultsList.appendChild(item);
        });
    }
    
    // Data loading functions
    async function loadProjects() {
        ui.projectsContainer.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"></div></div>';
        const result = await api.getProjects();
        
        if (result.success) {
            state.projects = result.projects;
            renderProjects(state.projects);
        } else {
            ui.projectsContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Failed to load projects. Please try again.
                    </div>
                </div>
            `;
        }
    }
    
    async function loadProject(projectId) {
        const result = await api.getProject(projectId);
        
        if (result.success) {
            state.currentProject = result.project;
            state.files = result.project.files;
            
            // Update UI
            ui.projectsSection.classList.add('d-none');
            ui.projectDetailSection.classList.remove('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.add('d-none');
            
            ui.projectDetailName.textContent = state.currentProject.name;
            ui.projectDetailDescription.textContent = state.currentProject.description || 'No description';
            
            renderFiles(state.files);
        }
    }
    
    async function loadFile(fileId) {
        const result = await api.getFile(fileId);
        
        if (result.success) {
            state.currentFile = result.file;
            
            // Update UI
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.remove('d-none');
            
            ui.fileDetailName.textContent = state.currentFile.filename;
            ui.fileLastUpdated.textContent = new Date(state.currentFile.updated_at).toLocaleString();
            
            // Setup file view based on type
            if (state.currentFile.file_type === 'text') {
                ui.textFileView.classList.remove('d-none');
                ui.imageFileView.classList.add('d-none');
                ui.fileContent.textContent = state.currentFile.content;
                ui.editFile.parentElement.classList.remove('d-none');
                ui.enhanceImage.parentElement.classList.add('d-none');
            } else if (state.currentFile.file_type === 'image') {
                ui.textFileView.classList.add('d-none');
                ui.imageFileView.classList.remove('d-none');
                ui.fileImage.src = `/api/files/${fileId}/content`;
                ui.editFile.parentElement.classList.add('d-none');
                ui.enhanceImage.parentElement.classList.remove('d-none');
            } else {
                ui.textFileView.classList.add('d-none');
                ui.imageFileView.classList.add('d-none');
                ui.editFile.parentElement.classList.add('d-none');
                ui.enhanceImage.parentElement.classList.add('d-none');
            }
            
            // Render versions
            renderFileVersions(state.currentFile.versions || []);
        }
    }
    
    // Initialize the application
    async function initialize() {
        console.log("Initializing application...");
        
        // Check if user is logged in
        const authStatus = await api.checkAuthStatus();
        console.log("Auth status:", authStatus);
        
        if (authStatus.logged_in) {
            state.currentUser = {
                id: authStatus.user_id,
                username: authStatus.username
            };
            
            ui.authSection.classList.add('d-none');
            ui.authButtons.classList.add('d-none');
            ui.userInfo.classList.remove('d-none');
            ui.usernameDisplay.textContent = authStatus.username;
            
            ui.projectsSection.classList.remove('d-none');
            loadProjects();
        } else {
            // Make sure the auth section is visible and forms are reset
            ui.authSection.classList.remove('d-none');
            ui.projectsSection.classList.add('d-none');
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.add('d-none');
            
            ui.loginForm.reset();
            ui.registerForm.reset();
            
            console.log("User not logged in, showing auth section");
        }
        
        // Set up event listeners
        
        // Auth
        ui.loginForm.addEventListener('submit', handlers.handleLogin);
        ui.registerForm.addEventListener('submit', handlers.handleRegister);
        ui.loginButton.addEventListener('click', () => {
            ui.authSection.classList.remove('d-none');
            ui.projectsSection.classList.add('d-none');
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.add('d-none');
            ui.loginTab.click();
        });
        ui.registerButton.addEventListener('click', () => {
            ui.authSection.classList.remove('d-none');
            ui.projectsSection.classList.add('d-none');
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.add('d-none');
            ui.registerTab.click();
        });
        ui.logoutButton.addEventListener('click', handlers.handleLogout);
        
        if (ui.resetForm) {
            ui.resetForm.addEventListener('submit', handlers.handleResetPassword);
        }

        const forgotPasswordLink = document.getElementById('forgot-password-link');
        if (forgotPasswordLink && ui.resetTab) {
            forgotPasswordLink.addEventListener('click', (e) => {
                e.preventDefault();
                ui.resetTab.click();
            });
        }

        ui.loginTab.addEventListener('click', (e) => {
            e.preventDefault();
            ui.loginTab.classList.add('active');
            ui.registerTab.classList.remove('active');
            ui.resetTab.classList.remove('active');
            ui.loginForm.classList.remove('d-none');
            ui.registerForm.classList.add('d-none');
            ui.resetForm.classList.add('d-none');
            console.log("Switched to login tab");
        });

        ui.registerTab.addEventListener('click', (e) => {
            e.preventDefault();
            ui.registerTab.classList.add('active');
            ui.loginTab.classList.remove('active');
            ui.resetTab.classList.remove('active');
            ui.registerForm.classList.remove('d-none');
            ui.loginForm.classList.add('d-none');
            ui.resetForm.classList.add('d-none');
            console.log("Switched to register tab");
        });

        if (ui.resetTab) {
            ui.resetTab.addEventListener('click', (e) => {
                e.preventDefault();
                ui.resetTab.classList.add('active');
                ui.loginTab.classList.remove('active');
                ui.registerTab.classList.remove('active');
                ui.resetForm.classList.remove('d-none');
                ui.loginForm.classList.add('d-none');
                ui.registerForm.classList.add('d-none');
                console.log("Switched to reset tab");
            });
        }
        
        // Projects
        ui.createProjectButton.addEventListener('click', () => {
            ui.createProjectModal.show();
        });
        document.getElementById('import-github-button').addEventListener('click', handlers.handleImportFromGithub);
        ui.createProjectForm.addEventListener('submit', handlers.handleCreateProject);
        ui.backToProjects.addEventListener('click', () => {
            ui.projectDetailSection.classList.add('d-none');
            ui.projectsSection.classList.remove('d-none');
        });
        ui.editProject.addEventListener('click', () => {
            document.getElementById('edit-project-name').value = state.currentProject.name;
            document.getElementById('edit-project-description').value = state.currentProject.description || '';
            ui.editProjectModal.show();
        });
        ui.editProjectForm.addEventListener('submit', handlers.handleEditProject);
        ui.publishToGithub.addEventListener('click', handlers.handlePublishToGithub);
        ui.exportToPdf.addEventListener('click', handlers.handleExportToPdf);
        ui.deleteProject.addEventListener('click', handlers.handleDeleteProject);
        
        // Files
        ui.createTextFile.addEventListener('click', () => {
            ui.createTextFileModal.show();
        });
        ui.createTextFileForm.addEventListener('submit', handlers.handleCreateTextFile);
        ui.uploadFile.addEventListener('click', () => {
            ui.uploadFileModal.show();
        });
        ui.uploadFileForm.addEventListener('submit', handlers.handleUploadFile);
        ui.backToProject.addEventListener('click', () => {
            ui.fileDetailSection.classList.add('d-none');
            ui.projectDetailSection.classList.remove('d-none');
        });
        ui.editFile.addEventListener('click', () => {
            document.getElementById('edit-file-content').value = state.currentFile.content || '';
            document.getElementById('edit-file-commit').value = '';
            ui.editFileModal.show();
        });
        ui.editFileForm.addEventListener('submit', handlers.handleEditFile);
        ui.enhanceImage.addEventListener('click', () => {
            ui.enhanceImageModal.show();
        });
        ui.enhanceStableDiffusion.addEventListener('click', () => {
            handlers.handleEnhanceImage('stable_diffusion');
        });
        ui.enhanceOllama.addEventListener('click', () => {
            handlers.handleEnhanceImage('ollama');
        });
        ui.downloadFile.addEventListener('click', () => {
            window.open(`/api/files/${state.currentFile.id}/content`, '_blank');
        });
        ui.deleteFile.addEventListener('click', handlers.handleDeleteFile);
        
        // Search
        ui.navSearch.addEventListener('click', () => {
            ui.projectsSection.classList.add('d-none');
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.remove('d-none');
            ui.searchInput.focus();
        });
        ui.searchButton.addEventListener('click', handlers.handleSearch);
        ui.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                handlers.handleSearch(e);
            }
        });
        
        // Navigation
        ui.navProjects.addEventListener('click', () => {
            ui.projectDetailSection.classList.add('d-none');
            ui.fileDetailSection.classList.add('d-none');
            ui.searchSection.classList.add('d-none');
            ui.projectsSection.classList.remove('d-none');
            loadProjects();
        });
        
        console.log("App initialization complete");
    }
    
    // Run the application
    initialize();
});

// Enhanced Text File Functionality

// Function to handle text file creation with timestamps and signatures
function enhanceTextFileCreation() {
    // Get references to elements
    const createTextFileBtn = document.getElementById('create-text-file');
    const newTextFileBtn = document.querySelector('.btn-new-text-file');
    const textFileModal = document.getElementById('create-text-file-modal');
    const textFileForm = document.getElementById('create-text-file-form');
    const textFileContent = document.getElementById('text-file-content');
    const textFileEditor = document.getElementById('rich-text-editor');
    
    // Add timestamp button functionality
    const addTimestampBtn = document.getElementById('add-timestamp');
    if (addTimestampBtn) {
        addTimestampBtn.addEventListener('click', function() {
            const now = new Date();
            const timestamp = `[${now.toISOString().replace('T', ' ').slice(0, 19)}] `;
            
            // Insert at cursor position or append
            if (textFileEditor && textFileEditor.classList.contains('active')) {
                // Rich text editor is active
                insertIntoRichEditor(timestamp);
            } else {
                // Plain text area is active
                insertAtCursor(textFileContent, timestamp);
            }
        });
    }
    
    // Add signature button functionality
    const addSignatureBtn = document.getElementById('add-signature');
    if (addSignatureBtn) {
        addSignatureBtn.addEventListener('click', function() {
            const now = new Date();
            const username = document.getElementById('username-display').textContent || 'User';
            const signature = `\n\n--- Signed by ${username} at ${now.toLocaleString()} ---\n\n`;
            
            if (textFileEditor && textFileEditor.classList.contains('active')) {
                // Rich text editor is active
                insertIntoRichEditor(signature);
            } else {
                // Plain text area is active
                insertAtCursor(textFileContent, signature);
            }
        });
    }
    
    // Fix for the Create button
    if (textFileForm) {
        textFileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log("Text file form submitted");
            
            // Get the content from either rich editor or plain text
            let content = textFileContent.value;
            if (textFileEditor && textFileEditor.classList.contains('active')) {
                content = textFileEditor.innerHTML;
            }
            
            // Get filename
            const filename = document.getElementById('text-file-name').value;
            
            // Check if we're in a project context
            if (window.currentProject && window.currentProject.id) {
                submitTextFile(window.currentProject.id, filename, content);
            } else {
                console.error("No active project found");
                alert("Error: No active project. Please reload the page and try again.");
            }
        });
    }
    
    // Toggle between rich text and plain text
    const toggleEditorBtn = document.getElementById('toggle-editor');
    if (toggleEditorBtn) {
        toggleEditorBtn.addEventListener('click', function() {
            const richTextContainer = document.getElementById('rich-text-container');
            const plainTextContainer = document.getElementById('plain-text-container');
            
            if (richTextContainer.classList.contains('d-none')) {
                // Switch to rich text
                richTextContainer.classList.remove('d-none');
                plainTextContainer.classList.add('d-none');
                textFileEditor.innerHTML = convertToHtml(textFileContent.value);
                toggleEditorBtn.innerHTML = '<i class="fas fa-code"></i> Plain Text';
            } else {
                // Switch to plain text
                richTextContainer.classList.add('d-none');
                plainTextContainer.classList.remove('d-none');
                textFileContent.value = convertToPlainText(textFileEditor.innerHTML);
                toggleEditorBtn.innerHTML = '<i class="fas fa-pen-fancy"></i> Rich Text';
            }
        });
    }
    
    // Initialize the rich text toolbar buttons
    initRichTextEditor();
}

// Helper function to submit the text file
function submitTextFile(projectId, filename, content) {
    console.log(`Submitting file: ${filename} to project ${projectId}`);
    
    // If projectId is not valid, try to get it from URL or page
    if (!projectId) {
        projectId = getProjectIdFromPage();
        console.log(`Using project ID from page: ${projectId}`);
    }
    
    if (!projectId) {
        alert("Error: Could not determine project ID. Please reload the page and try again.");
        return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('content', content);
    
    // Send API request
    fetch(`/api/projects/${projectId}/files`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal and refresh file list
            const modal = bootstrap.Modal.getInstance(document.getElementById('create-text-file-modal'));
            if (modal) {
                modal.hide();
            }
            
            // Reset form
            document.getElementById('create-text-file-form').reset();
            
            // Reload project details to show the new file
            if (window.loadProject && typeof window.loadProject === 'function') {
                window.loadProject(projectId);
            } else {
                // Fallback to page refresh
                window.location.reload();
            }
        } else {
            alert('Failed to create file: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error creating file:', error);
        alert('Error creating file. Please try again.');
    });
}

// Helper function to get project ID from the page
function getProjectIdFromPage() {
    // Method 1: Try to extract from URL
    const urlPath = window.location.pathname;
    const projectUrlMatch = urlPath.match(/\/projects\/(\d+)/);
    if (projectUrlMatch && projectUrlMatch[1]) {
        return projectUrlMatch[1];
    }
    
    // Method 2: Check for project in state
    try {
        const stateElement = document.querySelector('[data-state]');
        if (stateElement && stateElement.dataset.state) {
            const state = JSON.parse(stateElement.dataset.state);
            if (state.currentProject && state.currentProject.id) {
                return state.currentProject.id;
            }
        }
    } catch (e) {
        console.error("Error parsing state:", e);
    }
    
    // Method 3: Look for project ID in headings or title
    const projectName = document.querySelector('h2');
    if (projectName && projectName.textContent.trim() === 'Test') {
        // This is the Test project, use ID 1 (or whatever your Test project ID is)
        return 1;
    }
    
    // Method 4: Check data attributes on buttons
    const projectButtons = document.querySelectorAll('[data-project-id]');
    if (projectButtons.length > 0) {
        return projectButtons[0].dataset.projectId;
    }
    
    // Method 5: Fallback - check page content for clues
    if (document.body.textContent.includes('Test project')) {
        return 1; // Assuming Test project has ID 1
    }
    
    // If all else fails
    return null;
}

// Helper function to insert text at cursor position
function insertAtCursor(textarea, text) {
    if (!textarea) return;
    
    const startPos = textarea.selectionStart;
    const endPos = textarea.selectionEnd;
    
    textarea.value = 
        textarea.value.substring(0, startPos) +
        text +
        textarea.value.substring(endPos, textarea.value.length);
    
    // Update cursor position
    textarea.selectionStart = textarea.selectionEnd = startPos + text.length;
    textarea.focus();
}

// Helper function for rich text editor
function insertIntoRichEditor(text) {
    const editor = document.getElementById('rich-text-editor');
    if (!editor) return;
    
    // Get selection and range
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        if (range.commonAncestorContainer.parentNode === editor || 
            editor.contains(range.commonAncestorContainer)) {
            
            // Create text node
            const textNode = document.createTextNode(text);
            range.deleteContents();
            range.insertNode(textNode);
            
            // Set cursor after inserted text
            range.setStartAfter(textNode);
            range.setEndAfter(textNode);
            selection.removeAllRanges();
            selection.addRange(range);
        } else {
            // If cursor is not in editor, append to end
            editor.appendChild(document.createTextNode(text));
        }
    } else {
        // No selection, append to end
        editor.appendChild(document.createTextNode(text));
    }
    editor.focus();
}

// Initialize rich text editor toolbar
function initRichTextEditor() {
    const editor = document.getElementById('rich-text-editor');
    if (!editor) return;
    
    // Make content editable
    editor.contentEditable = true;
    
    // Format buttons
    const boldBtn = document.getElementById('format-bold');
    const italicBtn = document.getElementById('format-italic');
    const underlineBtn = document.getElementById('format-underline');
    const h2Btn = document.getElementById('format-h2');
    const h3Btn = document.getElementById('format-h3');
    const ulBtn = document.getElementById('format-ul');
    const olBtn = document.getElementById('format-ol');
    
    if (boldBtn) {
        boldBtn.addEventListener('click', function() {
            document.execCommand('bold', false, null);
            editor.focus();
        });
    }
    
    if (italicBtn) {
        italicBtn.addEventListener('click', function() {
            document.execCommand('italic', false, null);
            editor.focus();
        });
    }
    
    if (underlineBtn) {
        underlineBtn.addEventListener('click', function() {
            document.execCommand('underline', false, null);
            editor.focus();
        });
    }
    
    if (h2Btn) {
        h2Btn.addEventListener('click', function() {
            document.execCommand('formatBlock', false, '<h2>');
            editor.focus();
        });
    }
    
    if (h3Btn) {
        h3Btn.addEventListener('click', function() {
            document.execCommand('formatBlock', false, '<h3>');
            editor.focus();
        });
    }
    
    if (ulBtn) {
        ulBtn.addEventListener('click', function() {
            document.execCommand('insertUnorderedList', false, null);
            editor.focus();
        });
    }
    
    if (olBtn) {
        olBtn.addEventListener('click', function() {
            document.execCommand('insertOrderedList', false, null);
            editor.focus();
        });
    }
}

// Convert plain text to HTML
function convertToHtml(text) {
    if (!text) return '';
    
    // Basic conversion
    let html = text;
    
    // Convert newlines to <br>
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Convert HTML to plain text
function convertToPlainText(html) {
    if (!html) return '';
    
    // Create a temporary div
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Get text content
    let text = tempDiv.textContent || tempDiv.innerText || '';
    
    return text;
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Rich Text Editor Toggle
    const richTextToggle = document.querySelector('.btn-rich-text, #toggle-editor, [aria-label="Rich Text"]');
    const richTextContainer = document.getElementById('rich-text-container');
    const plainTextContainer = document.getElementById('plain-text-container');
    const richTextEditor = document.getElementById('rich-text-editor');
    const plainTextEditor = document.getElementById('text-file-content');
    
    // Handle the rich text toggle button
    if (richTextToggle) {
        console.log('Rich text toggle button found:', richTextToggle);
        
        richTextToggle.addEventListener('click', function(e) {
            console.log('Rich text toggle clicked');
            e.preventDefault();
            
            const isRichTextMode = richTextContainer && !richTextContainer.classList.contains('d-none');
            
            if (isRichTextMode) {
                // Switch to plain text
                console.log('Switching to plain text mode');
                if (richTextContainer) richTextContainer.classList.add('d-none');
                if (plainTextContainer) plainTextContainer.classList.remove('d-none');
                
                // Convert rich text to plain text
                if (richTextEditor && plainTextEditor) {
                    let content = richTextEditor.innerHTML;
                    // Convert <br> to newlines
                    content = content.replace(/<br\s*\/?>/gi, '\n');
                    // Convert <div> or <p> to newlines
                    content = content.replace(/<div>/gi, '\n').replace(/<\/div>/gi, '');
                    content = content.replace(/<p>/gi, '').replace(/<\/p>/gi, '\n');
                    // Remove other HTML tags but keep their content
                    content = content.replace(/<[^>]*>/g, '');
                    // Fix double newlines
                    content = content.replace(/\n\n+/g, '\n\n');
                    
                    plainTextEditor.value = content;
                }
                
                // Update the button text
                richTextToggle.innerHTML = '<i class="fas fa-pen-fancy"></i> Rich Text';
                
            } else {
                // Switch to rich text
                console.log('Switching to rich text mode');
                if (richTextContainer) richTextContainer.classList.remove('d-none');
                if (plainTextContainer) plainTextContainer.classList.add('d-none');
                
                // Convert plain text to rich text
                if (richTextEditor && plainTextEditor) {
                    let content = plainTextEditor.value;
                    // Convert newlines to <br>
                    content = content.replace(/\n/g, '<br>');
                    richTextEditor.innerHTML = content;
                }
                
                // Update the button text
                richTextToggle.innerHTML = '<i class="fas fa-code"></i> Plain Text';
                
                // Focus the rich text editor
                if (richTextEditor) richTextEditor.focus();
            }
        });
    } else {
        console.warn('Rich text toggle button not found');
    }
    
    // Set up rich text formatting buttons
    setupRichTextFormatting();
});

// Rich text formatting functions
function setupRichTextFormatting() {
    const formatButtons = {
        'format-bold': 'bold',
        'format-italic': 'italic',
        'format-underline': 'underline',
        'format-h2': 'h2',
        'format-h3': 'h3',
        'format-ul': 'insertUnorderedList',
        'format-ol': 'insertOrderedList'
    };
    
    // Add event listeners to formatting buttons
    for (const [buttonId, command] of Object.entries(formatButtons)) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', function() {
                if (command === 'h2' || command === 'h3') {
                    document.execCommand('formatBlock', false, `<${command}>`);
                } else {
                    document.execCommand(command, false, null);
                }
                // Focus the editor after format change
                const editor = document.getElementById('rich-text-editor');
                if (editor) editor.focus();
            });
        }
    }
    
    // Set up the rich text editor to handle content editable
    const editor = document.getElementById('rich-text-editor');
    if (editor) {
        editor.addEventListener('keydown', function(e) {
            // Ensure when Enter is pressed we create a <br> not a <div>
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.execCommand('insertLineBreak');
            }
        });
    }
}

// Export window.currentProject globally for direct access
window.currentProject = {
    id: getProjectIdFromPage()
};

console.log("Project ID detection initialized:", window.currentProject.id);

