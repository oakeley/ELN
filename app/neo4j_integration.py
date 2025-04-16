from py2neo import Graph, Node, Relationship
from flask import current_app
import json

class Neo4jIntegration:
    def __init__(self):
        """Initialize Neo4j connection using app configuration"""
        self.uri = current_app.config['NEO4J_URI']
        self.user = current_app.config['NEO4J_USER']
        self.password = current_app.config['NEO4J_PASSWORD']
        self.graph = Graph(uri=self.uri, user=self.user, password=self.password)
    
    def create_user_node(self, user_id, username):
        """Create a user node in Neo4j"""
        query = """
        MERGE (u:User {user_id: $user_id, username: $username})
        RETURN u
        """
        result = self.graph.run(query, user_id=user_id, username=username).data()
        return result[0]['u'] if result else None
    
    def create_project_node(self, project_id, name, description, user_id):
        """Create a project node in Neo4j and link to user"""
        # Create project node
        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (p:Project {project_id: $project_id, name: $name, description: $description})
        MERGE (u)-[:OWNS]->(p)
        RETURN p
        """
        result = self.graph.run(query, 
                               project_id=project_id, 
                               name=name, 
                               description=description, 
                               user_id=user_id).data()
        return result[0]['p'] if result else None
    
    def create_file_node(self, file_id, filename, file_type, content, project_id):
        """Create a file node in Neo4j and link to project"""
        # Create file node
        query = """
        MATCH (p:Project {project_id: $project_id})
        MERGE (f:File {file_id: $file_id, filename: $filename, file_type: $file_type})
        SET f.content = $content
        MERGE (p)-[:CONTAINS]->(f)
        RETURN f
        """
        result = self.graph.run(query, 
                               file_id=file_id, 
                               filename=filename, 
                               file_type=file_type, 
                               content=content, 
                               project_id=project_id).data()
        return result[0]['f'] if result else None
    
    def create_version_node(self, version_id, version_number, content, commit_message, file_id):
        """Create a version node in Neo4j and link to file"""
        query = """
        MATCH (f:File {file_id: $file_id})
        MERGE (v:Version {version_id: $version_id, version_number: $version_number, commit_message: $commit_message})
        SET v.content = $content
        MERGE (f)-[:HAS_VERSION]->(v)
        RETURN v
        """
        result = self.graph.run(query, 
                               version_id=version_id, 
                               version_number=version_number, 
                               content=content, 
                               commit_message=commit_message, 
                               file_id=file_id).data()
        return result[0]['v'] if result else None
    
    def add_keyword_to_file(self, file_id, keyword):
        """Add a keyword node and link to a file"""
        query = """
        MATCH (f:File {file_id: $file_id})
        MERGE (k:Keyword {name: $keyword})
        MERGE (f)-[:HAS_KEYWORD]->(k)
        RETURN k
        """
        result = self.graph.run(query, file_id=file_id, keyword=keyword).data()
        return result[0]['k'] if result else None
    
    def add_keywords_from_content(self, file_id, content, keywords):
        """Add keywords extracted from content and link to a file"""
        for keyword in keywords:
            self.add_keyword_to_file(file_id, keyword)
    
    def find_related_files(self, keywords, limit=10):
        """Find files related to the given keywords"""
        query = """
        MATCH (f:File)-[:HAS_KEYWORD]->(k:Keyword)
        WHERE k.name IN $keywords
        WITH f, COUNT(DISTINCT k) as relevance
        ORDER BY relevance DESC
        LIMIT $limit
        MATCH (p:Project)-[:CONTAINS]->(f)
        RETURN p.name as project_name, f.filename as filename, f.file_id as file_id, relevance
        """
        result = self.graph.run(query, keywords=keywords, limit=limit).data()
        return result
    
    def find_connections_between_files(self, file_id1, file_id2):
        """Find connections between two files through common keywords or other relationships"""
        query = """
        MATCH (f1:File {file_id: $file_id1})-[:HAS_KEYWORD]->(k:Keyword)<-[:HAS_KEYWORD]-(f2:File {file_id: $file_id2})
        RETURN k.name as connection, COUNT(k) as weight
        ORDER BY weight DESC
        """
        result = self.graph.run(query, file_id1=file_id1, file_id2=file_id2).data()
        return result
