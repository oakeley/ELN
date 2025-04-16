// Main JavaScript for Electronic Laboratory Notebook

document.addEventListener('DOMContentLoaded', () => {
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
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                return await response.json();
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
        
        async handleRegister(e) {
            e.preventDefault();
            
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            
            const result = await api.register(username, email, password);
            
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
                                    'Please run the setup script:\n' +
                                    'python scripts/setup_github_ssh.py\n\n' +
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
            const relevanceScore = result.relevance_score.toFixed(1);
            
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
            
            // Add open project handler
            const openButton = item.querySelector('button');
            openButton.addEventListener('click', () => {
                loadProject(project.id);
                ui.searchSection.classList.add('d-none');
                ui.projectDetailSection.classList.remove('d-none');
            });
            
            ui.searchResultsList.appendChild(item);
        });
    }
    
    // Data loading functions
    async function loadProjects() {
        const result = await api.getProjects();
        
        if (result.success) {
            state.projects = result.projects;
            renderProjects(state.projects);
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
                ui.editFile.classList.remove('d-none');
                ui.enhanceImage.classList.add('d-none');
            } else if (state.currentFile.file_type === 'image') {
                ui.textFileView.classList.add('d-none');
                ui.imageFileView.classList.remove('d-none');
                ui.fileImage.src = `/api/files/${fileId}/content`;
                ui.editFile.classList.add('d-none');
                ui.enhanceImage.classList.remove('d-none');
            } else {
                ui.textFileView.classList.add('d-none');
                ui.imageFileView.classList.add('d-none');
                ui.editFile.classList.add('d-none');
                ui.enhanceImage.classList.add('d-none');
            }
            
            // Render versions
            renderFileVersions(state.currentFile.versions || []);
        }
    }
    
    // Initialize the application
    async function initialize() {
        // Check if user is logged in
        const authStatus = await api.checkAuthStatus();
        
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
        }
        
        // Set up event listeners
        
        // Auth
        ui.loginForm.addEventListener('submit', handlers.handleLogin);
        ui.registerForm.addEventListener('submit', handlers.handleRegister);
        ui.loginButton.addEventListener('click', () => {
            ui.authSection.classList.remove('d-none');
            ui.loginTab.click();
        });
        ui.registerButton.addEventListener('click', () => {
            ui.authSection.classList.remove('d-none');
            ui.registerTab.click();
        });
        ui.logoutButton.addEventListener('click', handlers.handleLogout);
        
        ui.loginTab.addEventListener('click', (e) => {
            e.preventDefault();
            ui.loginTab.classList.add('active');
            ui.registerTab.classList.remove('active');
            ui.loginForm.classList.remove('d-none');
            ui.registerForm.classList.add('d-none');
        });
        
        ui.registerTab.addEventListener('click', (e) => {
            e.preventDefault();
            ui.registerTab.classList.add('active');
            ui.loginTab.classList.remove('active');
            ui.registerForm.classList.remove('d-none');
            ui.loginForm.classList.add('d-none');
        });
        
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
    }
    
    // Run the application
    initialize();
