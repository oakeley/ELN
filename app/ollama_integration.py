import requests
import json
import base64
from flask import current_app
import os
import time

class OllamaIntegration:
    def __init__(self):
        """Initialize Ollama API connection using app configuration"""
        self.api_url = current_app.config['OLLAMA_API_URL']
        self.model = current_app.config['OLLAMA_MODEL']
    
    def generate_text(self, prompt, max_tokens=1000):
        """Generate text using Ollama model"""
        try:
            payload = {
                'model': self.model,
                'prompt': prompt,
                'max_tokens': max_tokens,
                'stream': False
            }
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'text': response.json().get('response', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_image(self, image_path):
        """Analyze an image using Ollama multimodal capabilities"""
        try:
            # Read the image file
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
            
            # Base64 encode the image
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Create the prompt for image analysis
            prompt = "Analyze this image and describe what you see. Extract any visible text, describe key elements, and identify potential scientific content."
            
            payload = {
                'model': self.model,
                'prompt': prompt,
                'images': [img_base64],
                'stream': False
            }
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'analysis': response.json().get('response', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_keywords(self, text, max_keywords=10):
        """Extract keywords from text using Ollama model"""
        try:
            prompt = f"""Extract up to {max_keywords} scientific or technical keywords from the following text. 
            Return only a comma-separated list of individual words or short phrases without numbering or explanation:
            
            {text}"""
            
            result = self.generate_text(prompt, max_tokens=200)
            
            if result['success']:
                # Parse the comma-separated keywords
                keywords = [kw.strip() for kw in result['text'].split(',')]
                # Remove any empty strings
                keywords = [kw for kw in keywords if kw]
                # Limit to max_keywords
                keywords = keywords[:max_keywords]
                
                return {
                    'success': True,
                    'keywords': keywords
                }
            else:
                return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_connections(self, text1, text2):
        """Find connections between two texts using Ollama model"""
        try:
            prompt = f"""Compare the following two texts and identify any connections, 
            similarities, or complementary concepts between them. Return a list of specific connections:
            
            Text 1: {text1}
            
            Text 2: {text2}"""
            
            result = self.generate_text(prompt, max_tokens=500)
            
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def enhance_image_to_line_art(self, input_path, output_path):
        """Convert an image to vector-line art style using image prompt"""
        try:
            # Note: This is a simplified version assuming Ollama can do this
            # In a real implementation, you might need more complex processing
            
            # Read the image file
            with open(input_path, 'rb') as img_file:
                img_data = img_file.read()
            
            # Base64 encode the image
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Create the prompt for image enhancement
            prompt = "Convert this image to a clean vector line art style. Maintain the key features and details but create a simplified line drawing version suitable for a laboratory notebook."
            
            payload = {
                'model': self.model,
                'prompt': prompt,
                'images': [img_base64],
                'stream': False
            }
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                # In a real implementation, you would parse the response to get the processed image
                # For now, we'll just simulate this by copying the original image
                import shutil
                shutil.copy(input_path, output_path)
                
                return {
                    'success': True,
                    'file_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_projects(self, query_text, projects_data):
        """Search for relevant projects and files using semantic search"""
        try:
            # For each project, generate a comparison with the query
            results = []
            
            for project in projects_data:
                # Combine project name, description, and file info
                project_text = f"Project: {project['name']}\nDescription: {project['description']}\n"
                
                for file in project.get('files', []):
                    file_text = f"File: {file['filename']}\n"
                    if file.get('content'):
                        file_text += f"Content: {file['content'][:500]}...\n"
                    project_text += file_text
                
                # Create prompt to determine relevance
                prompt = f"""On a scale of 0 to 10, how relevant is the following research project to this query: "{query_text}"?
                
                {project_text}
                
                Return only a number from 0 to 10, where 10 is highly relevant and 0 is not relevant at all."""
                
                # Get relevance score
                response = self.generate_text(prompt, max_tokens=100)
                
                if response['success']:
                    try:
                        # Extract the numeric score
                        score_text = response['text'].strip()
                        # Find the first number in the response
                        import re
                        score_match = re.search(r'\d+(\.\d+)?', score_text)
                        
                        if score_match:
                            score = float(score_match.group())
                            # Only include if score is above threshold
                            if score > 3:  # Adjust threshold as needed
                                results.append({
                                    'project': project,
                                    'relevance_score': score
                                })
                    except Exception as parse_err:
                        # If parsing fails, use a default score
                        results.append({
                            'project': project,
                            'relevance_score': 5.0,  # Default middle score
                            'parse_error': str(parse_err)
                        })
            
            # Sort results by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'success': True,
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
