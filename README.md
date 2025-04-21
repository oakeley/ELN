# Electronic Laboratory Notebook for Programmers

A comprehensive web-based laboratory notebook system for research documentation with GitHub SSH integration, AI-powered search, and PDF export capabilities.

## Features

- **Project Management**: Organize your research into projects
- **File Management**: Store text notes and experimental images
- **Version Control**: Track all changes to files with automatic versioning
- **GitHub Integration**: Securely sync projects with GitHub repositories using SSH
- **AI-Powered Search**: Find connections between projects using the Ollama model
- **Neo4j Graph Database**: Store relationships between research elements
- **Image Enhancement**: Process images with Stable Diffusion or Ollama
- **PDF Export**: Generate professional reports with LaTeX

## System Requirements

- Python 3.8+
- Neo4j Database
- LaTeX (texlive packages for PDF export)
- Ollama with mistral-small3.1 model (optional)
- Stable Diffusion (optional)
- Git and SSH keys for GitHub integration

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/oakeley/ELN.git
   cd ELN
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   or...

   ```bash
   conda env create -f eln.yml
   conda activate eln
   ```

3. Install LaTeX dependencies (required for PDF export):
   
   On Ubuntu/Debian:
   ```bash
   sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-fonts-extra texlive-latex-extra
   ```
   
   On macOS (using Homebrew):
   ```bash
   brew install --cask mactex
   ```
   
   On Windows:
   - Install MiKTeX or TeX Live from their official websites

4. Set up SSH for GitHub:
   ```bash
   python scripts/setup_github_ssh.py
   ```
   This script will:
   - Check for existing SSH keys
   - Generate new keys if needed
   - Guide you through adding them to GitHub
   - Test the connection

5. Configure environment variables:
   ```bash
   cp env.example .env
   ```
   Edit the `.env` file to set:
   - `GITHUB_USERNAME`: Your GitHub username
   - `GITHUB_SSH_KEY_PATH`: Path to your SSH private key (default: `~/.ssh/id_ed25519`)
   - `GITHUB_SSH_PUB_KEY_PATH`: Path to your SSH public key (default: `~/.ssh/id_ed25519.pub`)
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j database connection details
   - `GIT_USER_NAME`, `GIT_USER_EMAIL`: Git configuration for commits

6. Run the application:
   ```bash
   python run.py
   ```

7. Access the application at: [http://localhost:5000](http://localhost:5000)

## Testing

The application comes with a comprehensive test suite covering various aspects of functionality:

### Running Tests

Run all tests:
```bash
python -m unittest discover tests
```

Run specific test files:
```bash
python -m unittest tests/test_database.py
python -m unittest tests/test_github.py
python -m unittest tests/test_integration.py
python -m unittest tests/test_routes.py
```

### Testing PDF Export

A dedicated script is provided to test the PDF export functionality in isolation:

```bash
python app/test_pdf_export.py
```

This script:
- Creates a test project with sample files
- Generates a PDF using the LaTeX export system
- Verifies PDF generation works correctly
- Saves the output as `test_output.pdf` for inspection
- Helps diagnose LaTeX-related issues without needing the full application

### Test Coverage

The test suite includes:

1. **Database Model Tests** (`test_database.py`)
   - Tests all database models and their relationships
   - Validates model attributes and behaviors
   - Tests cascade operations and integrity constraints
   - Ensures proper versioning of files

2. **GitHub Integration Tests** (`test_github.py`)
   - Tests SSH key verification
   - Tests repository creation, checking, and deletion
   - Tests project publishing to GitHub
   - Tests importing projects from GitHub repositories
   - Validates handling of various GitHub URL formats

3. **API Route Tests** (`test_routes.py`)
   - Tests all API endpoints
   - Validates authentication and authorization
   - Tests file operations (create, read, update, delete)
   - Tests project management functionality
   - Tests image enhancement and PDF export endpoints
   - Verifies proper error handling

4. **Integration Tests** (`test_integration.py`)
   - Tests cross-component workflows
   - Validates the interaction between different system parts
   - Tests end-to-end user workflows
   - Ensures components work together correctly

5. **PDF Export Tests** (`test_pdf_export.py`)
   - Tests LaTeX template rendering
   - Tests PDF generation with pdflatex
   - Tests handling of text and image files
   - Verifies PDF merging functionality

### Testing External Services

The tests use mocks for external services:
- Neo4j database operations
- GitHub API and Git operations
- Ollama AI model interactions
- Filesystem operations for files and images

This approach ensures tests are reliable and don't require external services to be running.

## GitHub SSH Authentication

This application uses SSH for secure GitHub authentication instead of personal access tokens. Benefits include:

- **Enhanced Security**: SSH keys are more secure than passwords or tokens
- **No Token Expiration**: SSH keys don't expire like personal access tokens
- **Simplified Workflow**: Once set up, no need to manage or rotate tokens
- **Standard Protocol**: Uses the same authentication method as Git command-line tools

SSH key authentication is handled through the underlying Git commands, providing a seamless experience without storing credentials in the application.

## Directory Structure

```
electronic-lab-notebook/
├── app/                      # Main application package
│   ├── static/               # Static assets (CSS, JavaScript)
│   ├── templates/            # HTML templates
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── routes.py             # API endpoints
│   ├── github_integration.py # GitHub SSH integration
│   ├── neo4j_integration.py  # Neo4j database integration
│   ├── ollama_integration.py # Ollama AI integration
│   ├── latex_export.py       # PDF export functionality
│   └── test_pdf_export.py    # PDF export test script
├── scripts/                  # Utility scripts
│   └── setup_github_ssh.py   # GitHub SSH setup script
├── tests/                    # Test suite
│   ├── test_database.py      # Database model tests
│   ├── test_github.py        # GitHub integration tests
│   ├── test_routes.py        # API endpoint tests
│   └── test_integration.py   # Cross-component integration tests
├── config.py                 # Application configuration
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

## Configuration

### LaTeX Configuration

For PDF export to work properly:

1. Ensure LaTeX (texlive) is installed on your system
2. The following packages are required:
   - texlive-latex-base (core LaTeX functionality)
   - texlive-fonts-recommended (standard fonts)
   - texlive-fonts-extra (additional fonts)
   - texlive-latex-extra (additional packages including 'pdfpages' for PDF merging)
3. You can test your LaTeX setup using the provided `test_pdf_export.py` script

### SSH Key Setup

For GitHub integration to work properly, you need to:

1. Have SSH keys generated on your system
2. Add your public key to your GitHub account
3. Ensure the SSH keys are specified in the `.env` file

If you already have SSH keys set up for GitHub, you can use those by specifying their path in the `.env` file.

### Neo4j Database

The application uses Neo4j to store relationships between projects, files, and keywords. You need a running Neo4j instance with the following configuration:

- **URI**: `bolt://localhost:7687` (default)
- **Username**: `neo4j` (default)
- **Password**: Specified in `.env` file

### Ollama Integration

For AI features like semantic search and image enhancement, you need:

1. Ollama installed and running
2. The mistral-small3.1 model loaded
3. Ollama API available at `http://localhost:11434/api/generate` (default)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GPL-3.0 - see the LICENSE file for details.
