/**
 * Electronic Laboratory Notebook - Frontend Tests
 * 
 * This file contains client-side tests for the Electronic Laboratory Notebook.
 * It validates core functionality of the frontend application.
 */

// Run tests when the window loads and the main.js has initialized
document.addEventListener('DOMContentLoaded', function() {
    // Only run tests in development mode, if enabled
    if (!window.location.search.includes('runTests=true')) {
        return;
    }

    console.log('=== Running Frontend Tests ===');
    
    // Test suite container
    const tests = {
        results: {
            passed: 0,
            failed: 0,
            total: 0
        },
        
        // Test utilities
        assert: function(condition, message) {
            this.results.total++;
            
            if (condition) {
                console.log(`✓ PASS: ${message}`);
                this.results.passed++;
                return true;
            } else {
                console.error(`✗ FAIL: ${message}`);
                this.results.failed++;
                return false;
            }
        },
        
        // Run all tests
        runAll: function() {
            console.log('Running UI component tests...');
            this.testUIComponents();
            
            console.log('Running API interface tests...');
            this.testAPIMethods();
            
            console.log('Running form validation tests...');
            this.testFormValidation();
            
            // Print summary
            console.log(`\n=== Test Summary ===`);
            console.log(`Passed: ${this.results.passed}/${this.results.total} (${Math.round(this.results.passed/this.results.total*100)}%)`);
            console.log(`Failed: ${this.results.failed}`);
            
            // Display result in UI if in test mode
            this.displayTestResults();
        },
        
        // Test UI components
        testUIComponents: function() {
            // Test that all required UI components exist
            this.assert(
                document.getElementById('auth-section') !== null,
                'Auth section exists'
            );
            
            this.assert(
                document.getElementById('projects-section') !== null,
                'Projects section exists'
            );
            
            this.assert(
                document.getElementById('login-form') !== null,
                'Login form exists'
            );
            
            this.assert(
                document.getElementById('create-project-button') !== null,
                'Create project button exists'
            );
            
            this.assert(
                document.getElementById('import-github-button') !== null,
                'Import from GitHub button exists'
            );
            
            // Test modal dialogs
            const createProjectModal = new bootstrap.Modal(document.getElementById('create-project-modal'));
            this.assert(
                typeof createProjectModal.show === 'function',
                'Create project modal can be initialized'
            );
        },
        
        // Test API methods
        testAPIMethods: function() {
            // Check that the API methods exist in the main.js file
            if (typeof api !== 'undefined') {
                this.assert(
                    typeof api.login === 'function',
                    'API login method exists'
                );
                
                this.assert(
                    typeof api.getProjects === 'function',
                    'API getProjects method exists'
                );
                
                this.assert(
                    typeof api.createProject === 'function',
                    'API createProject method exists'
                );
                
                this.assert(
                    typeof api.verifyGithubSSH === 'function',
                    'API verifyGithubSSH method exists'
                );
                
                this.assert(
                    typeof api.search === 'function',
                    'API search method exists'
                );
            } else {
                this.assert(false, 'API object exists in global scope');
            }
        },
        
        // Test form validation
        testFormValidation: function() {
            // Test the login form validation
            const loginForm = document.getElementById('login-form');
            const loginUsernameInput = document.getElementById('login-username');
            const loginPasswordInput = document.getElementById('login-password');
            
            if (loginForm && loginUsernameInput && loginPasswordInput) {
                // Test valid input
                loginUsernameInput.value = 'testuser';
                loginPasswordInput.value = 'password123';
                
                this.assert(
                    loginForm.checkValidity(),
                    'Login form validates with correct input'
                );
                
                // Test invalid input
                loginUsernameInput.value = '';
                
                this.assert(
                    !loginForm.checkValidity(),
                    'Login form fails validation with empty username'
                );
            }
            
            // Test the project creation form validation
            const createProjectForm = document.getElementById('create-project-form');
            const projectNameInput = document.getElementById('project-name');
            
            if (createProjectForm && projectNameInput) {
                // Test valid input
                projectNameInput.value = 'Test Project';
                
                this.assert(
                    createProjectForm.checkValidity(),
                    'Create project form validates with correct input'
                );
                
                // Test invalid input
                projectNameInput.value = '';
                
                this.assert(
                    !createProjectForm.checkValidity(),
                    'Create project form fails validation with empty name'
                );
            }
        },
        
        // Display test results in UI
        displayTestResults: function() {
            // Create a test results banner
            const resultsDiv = document.createElement('div');
            resultsDiv.className = 'test-results fixed-bottom p-2 text-center';
            resultsDiv.style.backgroundColor = this.results.failed > 0 ? '#ffdddd' : '#ddffdd';
            resultsDiv.style.borderTop = '1px solid ' + (this.results.failed > 0 ? '#ff0000' : '#00ff00');
            
            resultsDiv.innerHTML = `
                <strong>Frontend Tests:</strong> 
                ${this.results.passed}/${this.results.total} passed 
                (${Math.round(this.results.passed/this.results.total*100)}%)
                ${this.results.failed > 0 ? `<span style="color:red"> - ${this.results.failed} failed</span>` : ''}
                <button class="btn btn-sm btn-outline-dark ms-3" onclick="this.parentNode.remove()">Dismiss</button>
            `;
            
            document.body.appendChild(resultsDiv);
        }
    };
    
    // Run tests after a slight delay to ensure everything has loaded
    setTimeout(() => {
        tests.runAll();
    }, 500);
});
