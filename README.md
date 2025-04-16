# Electronic Laboratory Notebook for Programmers

This implementation provides a fully functional Electronic Laboratory Notebook system with the following features:

## Key Components

1. **Web-Based Front End**
   - Modern responsive UI using Bootstrap 5
   - JavaScript-based single-page application
   - Interactive project and file management

2. **Backend API**
   - RESTful Flask API for data management
   - Authentication system with user accounts
   - File upload and management
   - Project organization

3. **Database Integration**
   - SQLAlchemy for relational data storage
   - Neo4j for graph-based data connections and search
   - Version control for all file changes

4. **GitHub Integration**
   - Publish projects to GitHub repositories
   - Import projects from existing GitHub repositories
   - Synchronize changes between local projects and GitHub

5. **Ollama AI Integration**
   - Semantic search across projects and files
   - Image analysis and enhancement
   - Keyword extraction for better organization
   - Connection discovery between related projects

6. **PDF Export via LaTeX**
   - Professional PDF report generation
   - Customizable LaTeX template
   - Support for text and image content

## System Architecture

The system follows a classic MVC architecture:

- **Models**: SQLAlchemy models for users, projects, files, and versions
- **Views**: HTML templates with Bootstrap styling
- **Controllers**: Flask routes handling API endpoints

Neo4j provides a graph database layer that enhances the system with:
- Knowledge graph capabilities
- Semantic connections between projects and files
- Enhanced search functionality

The Ollama integration (mistral-small3.1 model) provides AI capabilities:
- Text analysis and comprehension
- Multimodal image analysis
- Vector-based search
- Natural language processing

## Implementation Details

The project is organized into a cohesive structure:
```
electronic-lab-notebook/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   └── tests.js
│   │   └── uploads/
│   ├── templates/
│   │   ├── index.html
│   │   └── latex_template.tex
│   ├── __init__.py
│   ├── models.py
│   ├── utils.py
│   ├── routes.py
│   ├── github_integration.py
│   ├── neo4j_integration.py
│   ├── ollama_integration.py
│   └── latex_export.py
├── tests/
│   ├── test_routes.py
│   ├── test_database.py
│   ├── test_github.py
│   └── test_integration.py
├── config.py
├── requirements.txt
└── run.py
```

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Setup environment variables:
   - Create a `.env` file with the following settings:
     ```
     SECRET_KEY=your-secret-key
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USER=neo4j
     NEO4J_PASSWORD=your-password
     GITHUB_TOKEN=your-github-token
     OLLAMA_API_URL=http://localhost:11434/api/generate
     ```

3. Initialize the database:
   - Make sure Neo4j is running
   - The SQLite database will be created automatically on first run

4. Run the application:
   ```
   python run.py
   ```

5. Access the application at `http://localhost:5000`

## Future Enhancements

1. Add support for more file types and formats
2. Implement collaborative features (multiple users on one project)
3. Add advanced visualization for scientific data
4. Implement automated backups
5. Add support for external storage providers
6. Enhance security with two-factor authentication
