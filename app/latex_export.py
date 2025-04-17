from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import tempfile
import shutil
from flask import current_app
import re

class LatexExport:
    def __init__(self):
        """Initialize LaTeX export functionality"""
        # Set up Jinja2 environment for LaTeX templates
        templates_path = os.path.join(current_app.root_path, 'templates')
        self.env = Environment(loader=FileSystemLoader(templates_path))
        
        # Set up LaTeX escape function
        self.env.filters['tex_escape'] = self.tex_escape
    
    @staticmethod
    def tex_escape(text):
        """Escape special LaTeX characters"""
        if text is None:
            return ""
        
        conv = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
            '<': r'\textless{}',
            '>': r'\textgreater{}',
        }
        regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=lambda item: -len(item))))
        return regex.sub(lambda match: conv[match.group()], text)
    
    def generate_latex(self, project, files):
        """Generate LaTeX code for a project"""
        # Get the template
        template = self.env.get_template('latex_template.tex')
        
        # Prepare project data for template
        project_data = {
            'title': project.name,
            'abstract': project.description or "No description provided.",
            'sections': [],
            'images': []
        }
        
        # Create temporary directory for images
        temp_dir = tempfile.mkdtemp()
        image_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_dir, exist_ok=True)
        
        # Process files
        for file in files:
            if file.file_type == 'text':
                # Add text files as sections
                project_data['sections'].append({
                    'title': file.filename,
                    'content': file.content or "No content available."
                })
            elif file.file_type == 'image':
                # Copy image to temp directory with a safe name
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                temp_image_path = os.path.join(image_dir, safe_name)
                
                try:
                    shutil.copy2(file.file_path, temp_image_path)
                    
                    # Add image files with LaTeX-safe path
                    project_data['images'].append({
                        'path': temp_image_path.replace('\\', '/'),  # Use forward slashes
                        'caption': self.tex_escape(file.filename)
                    })
                except Exception as e:
                    print(f"Error copying image {file.file_path}: {str(e)}")
        
        # Render the template
        try:
            latex_content = template.render(project=project_data)
            return latex_content
        except Exception as e:
            print(f"Error rendering LaTeX template: {str(e)}")
            raise
    
    def generate_pdf(self, latex_content, output_path=None):
        """Generate a PDF from LaTeX content"""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Write the LaTeX content to a file
            tex_file = os.path.join(temp_dir, 'output.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF
            # Run pdflatex twice to ensure references are correct
            for _ in range(2):
                process = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', tex_file],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            if process.returncode != 0:
                # If PDF generation failed, print error for debugging
                error_output = process.stdout.decode('utf-8') + process.stderr.decode('utf-8')
                print(f"PDF generation failed: {error_output}")
                return {
                    'success': False,
                    'error': error_output
                }
            
            # PDF was generated successfully
            pdf_file = os.path.join(temp_dir, 'output.pdf')
            
            if not os.path.exists(pdf_file):
                return {
                    'success': False,
                    'error': 'PDF file was not created'
                }
            
            if output_path:
                # Copy the PDF to the specified location
                shutil.copy(pdf_file, output_path)
                return {
                    'success': True,
                    'pdf_path': output_path
                }
            else:
                # Read the PDF content
                with open(pdf_file, 'rb') as f:
                    pdf_content = f.read()
                return {
                    'success': True,
                    'pdf_content': pdf_content
                }
        
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            # Always clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    def export_project_to_pdf(self, project, files, output_path=None):
        """Export a project to PDF"""
        try:
            # Generate LaTeX content
            latex_content = self.generate_latex(project, files)
            
            # Generate PDF
            return self.generate_pdf(latex_content, output_path)
        except Exception as e:
            print(f"Error in export_project_to_pdf: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
