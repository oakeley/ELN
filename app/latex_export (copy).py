import os
import re
import tempfile
import shutil
import subprocess
from flask import current_app
import json
from jinja2 import Template
import io
import traceback
import sys
import pprint

class LatexExport:
    def __init__(self):
        """Initialize LaTeX export functionality"""
        print("Initializing LatexExport instance")
        # Define the template file path
        self.template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'latex_template.tex')
        print(f"Template path set to: {self.template_path}")
        
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
    
    def load_template(self):
        """Load the LaTeX template from file"""
        try:
            # First check for template in the current directory
            template_paths = [
                self.template_path,  # Try the direct path first
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'latex_template.tex'),
            ]
            
            # Only try the Flask app paths if we're in an application context
            try:
                from flask import current_app
                if current_app:
                    template_paths.append(os.path.join(current_app.root_path, 'templates', 'latex_template.tex'))
                    template_paths.append(os.path.join(current_app.root_path, 'latex_template.tex'))
            except RuntimeError:
                # Not in a Flask app context, that's okay
                pass
            
            # Try all the paths
            for path in template_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            # If we can't find the template, use a built-in one
            return self._get_basic_template()
            
        except Exception as e:
            print(f"Error loading template: {str(e)}")
            return self._get_basic_template()
    
    def _get_basic_template(self):
        """Return a basic LaTeX template as fallback"""
        print("Using basic fallback LaTeX template")
        return r"""\documentclass[12pt]{article}
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{graphicx}

\begin{document}

\begin{center}
{\Large\bfseries {{ project.title }}}

\vspace{0.5cm}
{\large {{ project.abstract }}}
\end{center}

\vspace{1cm}

{% for section in project.sections %}
\section*{{{ section.title }}}
{{ section.content }}

{% endfor %}

\end{document}"""
    
    def generate_latex(self, project, files):
        """Generate LaTeX code for a project"""
        print(f"Starting LaTeX generation for project: {project.name}")
        # Load template
        template_content = self.load_template()
        
        # Create a template from the string
        template = Template(template_content)
        
        # Prepare project data for template
        project_data = {
            'title': self.tex_escape(project.name),
            'abstract': self.tex_escape(project.description or "No description provided."),
            'sections': [],
            'images': []
        }
        
        print(f"Project data initialized: {json.dumps(project_data, indent=2)}")
        
        # Create temporary directory for images
        temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {temp_dir}")
        
        image_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_dir, exist_ok=True)
        print(f"Created images directory: {image_dir}")
        
        # Process files
        print(f"Processing {len(files)} files for PDF export")
        for file in files:
            print(f"Processing file: {file.filename}, type: {file.file_type}")
            if file.file_type == 'text':
                # Add text files as sections
                print(f"Adding text file: {file.filename}")
                project_data['sections'].append({
                    'title': self.tex_escape(file.filename),
                    'content': self.tex_escape(file.content or "No content available.")
                })
                print(f"Added section for: {file.filename}")
            elif file.file_type == 'image':
                # Copy image to temp directory with a safe name
                print(f"Processing image file: {file.filename}")
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                temp_image_path = os.path.join(image_dir, safe_name)
                
                try:
                    print(f"Copying image from {file.file_path} to {temp_image_path}")
                    shutil.copy2(file.file_path, temp_image_path)
                    
                    # Add image files with LaTeX-safe path
                    image_path = os.path.join('images', safe_name).replace('\\', '/')
                    
                    print(f"Image copied to: {temp_image_path}")
                    print(f"LaTeX image path: {image_path}")
                    
                    project_data['images'].append({
                        'path': image_path,
                        'caption': self.tex_escape(file.filename)
                    })
                    print(f"Added image entry for: {file.filename}")
                except Exception as e:
                    print(f"Error copying image {file.file_path}: {str(e)}")
                    print(traceback.format_exc())
        
        # Render the template
        try:
            print("Rendering LaTeX template")
            latex_content = template.render(project=project_data)
            print(f"LaTeX content generated: {len(latex_content)} characters")
            # Write first 500 chars for debugging
            print(f"LaTeX content preview: {latex_content[:500]}...")
            return latex_content, temp_dir
        except Exception as e:
            print(f"Error rendering LaTeX template: {str(e)}")
            print(traceback.format_exc())
            shutil.rmtree(temp_dir)  # Clean up on error
            raise
    
    def generate_pdf(self, latex_content, temp_dir):
        """Generate a PDF from LaTeX content"""
        print("Starting PDF generation")
        try:
            # Write the LaTeX content to a file
            tex_file = os.path.join(temp_dir, 'output.tex')
            print(f"Writing LaTeX content to: {tex_file}")
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            print(f"LaTeX file created at: {tex_file}")
            print(f"Directory contents: {os.listdir(temp_dir)}")
            
            # Compile LaTeX to PDF
            for i in range(2):
                try:
                    print(f"Running pdflatex, attempt {i+1}")
                    process = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', tex_file],
                        cwd=temp_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=30
                    )
                    
                    print(f"pdflatex run {i+1} return code: {process.returncode}")
                    
                    if process.returncode != 0:
                        output = process.stdout.decode('utf-8', errors='replace')
                        error = process.stderr.decode('utf-8', errors='replace')
                        print(f"pdflatex stdout: {output[:500]}...")
                        print(f"pdflatex stderr: {error[:500]}...")
                except subprocess.TimeoutExpired:
                    print("pdflatex process timed out")
                    return {"success": False, "error": "PDF generation timed out"}
            
            if process.returncode != 0:
                error_output = process.stdout.decode('utf-8', errors='replace')
                print(f"PDF generation failed: {error_output[:500]}...")
                return {"success": False, "error": "PDF generation failed"}
            
            # Check if PDF was created
            pdf_file = os.path.join(temp_dir, 'output.pdf')
            print(f"Looking for PDF at: {pdf_file}")
            
            if not os.path.exists(pdf_file):
                print(f"PDF file not found at {pdf_file}")
                print(f"Directory contents: {os.listdir(temp_dir)}")
                return {"success": False, "error": "PDF file was not created"}
            
            # Read the PDF content
            print(f"PDF file found, reading content")
            with open(pdf_file, 'rb') as f:
                pdf_content = f.read()
            
            print(f"PDF content read, {len(pdf_content)} bytes")
            
            # Ensure we return a simple dictionary with serializable values
            result = {"success": True}
            
            # Store PDF content separately to avoid JSON serialization issues
            result["pdf_content"] = pdf_content
            
            print("PDF generation successful, returning result")
            print(f"Result keys: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def export_project_to_pdf(self, project, files, output_path=None):
        """Export a project to PDF"""
        print(f"Starting PDF export for project: {project.name}")
        temp_dir = None
        try:
            # Generate LaTeX content
            latex_content, temp_dir = self.generate_latex(project, files)
            
            # Generate PDF
            result = self.generate_pdf(latex_content, temp_dir)
            
            print(f"PDF generation result: success={result.get('success', False)}")
            
            # Make a copy of the result dictionary for JSON serialization
            json_safe_result = {"success": result.get("success", False)}
            
            # Add error message if present
            if "error" in result:
                json_safe_result["error"] = str(result["error"])
            
            # Handle output path if specified
            if output_path and result.get("success", False) and "pdf_content" in result:
                print(f"Writing PDF to output path: {output_path}")
                with open(output_path, 'wb') as f:
                    f.write(result["pdf_content"])
                json_safe_result["pdf_path"] = output_path
            
            # For binary content, we'll keep it separate from the JSON response
            if "pdf_content" in result and isinstance(result["pdf_content"], bytes):
                # Store PDF content in the original result but not in json_safe_result
                print("PDF content available but not included in JSON result")
                json_safe_result["pdf_content_available"] = True
            
            # Test JSON serialization to catch any issues
            try:
                print("Testing JSON serialization of result")
                json_str = json.dumps(json_safe_result)
                print(f"JSON serialization successful: {len(json_str)} characters")
            except Exception as e:
                print(f"JSON serialization failed: {str(e)}")
                print(f"Result structure: {pprint.pformat(json_safe_result)}")
                
                # Fall back to a minimal result with just success and error info
                json_safe_result = {
                    "success": False,
                    "error": f"JSON serialization error: {str(e)}"
                }
            
            # Combine original result with json_safe_result
            # This way, we keep the pdf_content for file sending, but have a clean dict for JSON
            for key, value in json_safe_result.items():
                if key != "pdf_content":  # Don't overwrite pdf_content
                    result[key] = value
            
            print(f"Final result keys: {list(result.keys())}")
            print(f"JSON-safe result keys: {list(json_safe_result.keys())}")
            
            # For debugging, set an attribute to distinguish between the original and JSON-safe results
            result["_json_safe"] = json_safe_result
            
            return result
            
        except Exception as e:
            print(f"Error in export_project_to_pdf: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
        finally:
            # Always clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    print(f"Cleaning up temp directory: {temp_dir}")
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Error cleaning up temp directory: {str(e)}")
